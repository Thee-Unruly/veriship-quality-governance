"""API endpoints for the Quality Copilot AI features."""

import json
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.config import settings
from app.models import Requirement, Release, Defect, DefectStatus, DefectSeverity
from app.schemas.copilot import (
    RequirementClarityAnalysis,
    TestCaseGenerationResult,
    ReleaseReadinessAnalysis,
    BlockingIssue
)

router = APIRouter()


def call_openrouter(api_key: str, user_message: str) -> str:
    """Call OpenRouter API with error handling."""
    try:
        response = requests.post(
            settings.openrouter_api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": settings.openrouter_site_url,
                "X-Title": settings.openrouter_site_name,
                "Content-Type": "application/json"
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {response.text}"
            )
        
        return response.json()["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call OpenRouter API: {str(e)}"
        )


@router.post(
    "/analyze-requirement-clarity/{requirement_id}",
    response_model=RequirementClarityAnalysis,
    summary="Analyzes a single requirement for clarity, testability, and completeness.",
    description="""
    Accepts a requirement ID, fetches the requirement text, and uses AI to perform
    a detailed analysis. The results are persisted back to the requirement's record.
    """
)
def analyze_requirement_clarity(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyzes the clarity of a specific requirement using OpenRouter AI.
    """
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Build AI prompt
    prompt = f"""Analyze the following requirement for clarity, testability, and completeness.
    
Requirement: {requirement.title}
Description: {requirement.description}

Provide a JSON response with these exact keys:
{{
    "clarity_score": <0-100>,
    "is_testable": <true/false>,
    "ambiguous_terms": [<list of unclear terms>],
    "missing_criteria": [<list of missing criteria>],
    "suggestions": [<list of improvement suggestions>]
}}

Only respond with valid JSON, no additional text."""

    try:
        ai_response = call_openrouter(
            settings.openrouter_clarity_api_key,
            prompt
        )
        
        # Extract JSON from response (sometimes models add extra text)
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            analysis_data = json.loads(json_str)
        else:
            analysis_data = json.loads(ai_response)
        
        analysis_result = RequirementClarityAnalysis(**analysis_data)
        
        # Save to database
        requirement.clarity_score = analysis_result.clarity_score
        requirement.is_testable = analysis_result.is_testable
        requirement.ambiguous_terms = analysis_result.ambiguous_terms
        requirement.missing_criteria = analysis_result.missing_criteria
        db.commit()
        db.refresh(requirement)
        
        return analysis_result
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )


@router.post(
    "/generate-test-cases/{requirement_id}",
    response_model=TestCaseGenerationResult,
    summary="Generates test case suggestions for a requirement.",
    description="""
    Accepts a requirement ID and uses AI to generate a list of suggested test cases.
    These are suggestions and are NOT automatically saved to the database.
    """
)
def generate_test_cases(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """
    Generates test case ideas for a specific requirement using OpenRouter AI.
    """
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Build AI prompt
    prompt = f"""Generate test cases for the following requirement:

Requirement: {requirement.title}
Description: {requirement.description}

Generate comprehensive test cases covering positive, negative, edge cases, etc.

Return a JSON response with this exact structure:
{{
    "generated_test_cases": [
        {{
            "title": "<test case title>",
            "description": "<brief purpose>",
            "test_type": "<Positive|Negative|Edge Case|Performance|Security>",
            "priority": <1-5>,
            "test_steps": ["<step 1>", "<step 2>", ...],
            "expected_result": "<expected outcome>"
        }}
    ]
}}

Generate at least 3-5 test cases. Only respond with valid JSON, no additional text."""

    try:
        ai_response = call_openrouter(
            settings.openrouter_testcase_api_key,
            prompt
        )
        
        # Extract JSON from response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            result_data = json.loads(json_str)
        else:
            result_data = json.loads(ai_response)
        
        return TestCaseGenerationResult(**result_data)
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )


@router.post(
    "/check-release-readiness/{release_id}",
    response_model=ReleaseReadinessAnalysis,
    summary="Performs a readiness check for a specific release.",
    description="""
    Accepts a release ID, fetches all related defects and requirements,
    and uses AI to determine a risk score and go/no-go decision.
    """
)
def check_release_readiness(
    release_id: int,
    db: Session = Depends(get_db)
):
    """
    Performs a readiness check for a specific release using OpenRouter AI.
    """
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # --- Data Aggregation ---
    # Find all open, critical defects for this release's project
    open_critical_defects = db.query(Defect).filter(and_(
        Defect.project_id == release.project_id,
        Defect.status.in_([DefectStatus.OPEN, DefectStatus.REOPENED]),
        Defect.severity == DefectSeverity.CRITICAL
    )).all()

    # Construct list of blocking issues
    blockers = [
        BlockingIssue(
            issue_type="Defect",
            identifier=d.defect_id,
            title=d.title,
            status=d.status.value,
            severity=d.severity.value
        ) for d in open_critical_defects
    ]

    # Build AI prompt with actual data
    defect_summary = "\n".join([
        f"- {d.defect_id}: {d.title} (Status: {d.status.value}, Severity: {d.severity.value})"
        for d in open_critical_defects
    ]) if open_critical_defects else "No critical defects found"

    prompt = f"""Analyze the release readiness for: {release.release_id} (Version: {release.version})

Critical Defects:
{defect_summary}

Test Coverage: {release.actual_test_coverage or 0}%
Requirements Met: {release.requirements_met}

Provide a JSON response with:
{{
    "risk_score": <0-100>,
    "go_no_go_decision": "<GO|NO-GO|CONDITIONAL>",
    "summary": "<brief assessment>"
}}

Only respond with valid JSON, no additional text."""

    try:
        ai_response = call_openrouter(
            settings.openrouter_clarity_api_key,  # Reuse clarity key for release analysis
            prompt
        )
        
        # Extract JSON from response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            analysis_data = json.loads(json_str)
        else:
            analysis_data = json.loads(ai_response)
        
        # Ensure risk_score is between 0 and 100
        risk_score = max(0, min(100, analysis_data.get("risk_score", 50)))
        
        # Update the release record in the database
        release.risk_score = risk_score
        release.go_no_go_decision = analysis_data.get("go_no_go_decision", "CONDITIONAL")
        release.blockers = [b.dict() for b in blockers]
        db.commit()
        db.refresh(release)

        return ReleaseReadinessAnalysis(
            release_id=release.release_id,
            risk_score=risk_score,
            go_no_go_decision=analysis_data.get("go_no_go_decision", "CONDITIONAL"),
            summary=analysis_data.get("summary", "Release readiness assessed by AI."),
            blockers=blockers
        )
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )


@router.get("/status")
def copilot_status():
    """Check the status of the Copilot endpoints."""
    return {"status": "Copilot is active"}