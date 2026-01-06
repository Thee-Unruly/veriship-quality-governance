"""API endpoints for the Quality Copilot AI features."""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import Requirement, Release, Defect, DefectStatus, DefectSeverity
from app.schemas.copilot import (
    RequirementClarityAnalysis,
    TestCaseGenerationResult,
    ReleaseReadinessAnalysis,
    BlockingIssue
)

router = APIRouter()

@router.post(
    "/analyze-requirement-clarity/{requirement_id}",
    response_model=RequirementClarityAnalysis,
    summary="Analyzes a single requirement for clarity, testability, and completeness.",
    description="""
    Accepts a requirement ID, fetches the requirement text, and uses an AI model
    (currently mocked) to perform a detailed analysis. The results are then
    persisted back to the requirement's record in the database.
    """
)
def analyze_requirement_clarity(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyzes the clarity of a specific requirement.
    """
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # --- AI Model Call (Mocked) ---
    time.sleep(2) # Simulate network latency of an API call

    mocked_analysis = {
        "clarity_score": 78.5,
        "is_testable": True,
        "ambiguous_terms": ["quickly", "user-friendly"],
        "missing_criteria": [
            "What is the expected response time for the system?",
            "How should the system handle invalid user inputs?"
        ],
        "suggestions": [
            "Replace 'quickly' with a specific time measurement (e.g., 'under 500ms').",
            "Define 'user-friendly' with concrete UI/UX behaviors."
        ]
    }
    # --- End Mocked Call ---

    analysis_result = RequirementClarityAnalysis(**mocked_analysis)
    requirement.clarity_score = analysis_result.clarity_score
    requirement.is_testable = analysis_result.is_testable
    requirement.ambiguous_terms = analysis_result.ambiguous_terms
    requirement.missing_criteria = analysis_result.missing_criteria
    db.commit()
    db.refresh(requirement)

    return analysis_result


@router.post(
    "/generate-test-cases/{requirement_id}",
    response_model=TestCaseGenerationResult,
    summary="Generates test case suggestions for a requirement.",
    description="""
    Accepts a requirement ID and uses an AI model (currently mocked) to generate
    a list of suggested test cases. These are suggestions and are NOT
    automatically saved to the database.
    """
)
def generate_test_cases(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """
    Generates test case ideas for a specific requirement.
    """
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # --- AI Model Call (Mocked) ---
    time.sleep(3)

    mocked_test_cases = {
        "generated_test_cases": [
            {
                "title": "TC-Positive: Successful Login with Valid Credentials",
                "description": "Verifies that a user can log in successfully.",
                "test_type": "Positive", "priority": 1,
                "test_steps": ["Navigate to login", "Enter valid credentials", "Click login"],
                "expected_result": "User is redirected to dashboard."
            },
            {
                "title": "TC-Negative: Failed Login with Invalid Password",
                "description": "Verifies that a user cannot log in with wrong password.",
                "test_type": "Negative", "priority": 2,
                "test_steps": ["Navigate to login", "Enter valid username", "Enter wrong password", "Click login"],
                "expected_result": "Error message is shown."
            }
        ]
    }
    # --- End Mocked Call ---

    return TestCaseGenerationResult(**mocked_test_cases)


@router.post(
    "/check-release-readiness/{release_id}",
    response_model=ReleaseReadinessAnalysis,
    summary="Performs a readiness check for a specific release.",
    description="""
    Accepts a release ID, fetches all related defects and requirements,
    and runs an analysis to determine a risk score and a go/no-go decision.
    """
)
def check_release_readiness(
    release_id: int,
    db: Session = Depends(get_db)
):
    """
    Performs a readiness check for a specific release.
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
    # In a real scenario, you'd also check for untested requirements, etc.

    # --- AI Synthesis (Mocked) ---
    time.sleep(2)
    risk_score = 85.0 if blockers else 35.0
    go_no_go = "NO-GO" if blockers else "GO"
    summary = f"Found {len(blockers)} critical blocking issue(s). Release is NOT recommended." if blockers else "No critical blockers found. Release is cleared to proceed."
    # --- End Mocked Call ---

    # Update the release record in the database
    release.risk_score = risk_score
    release.go_no_go_decision = go_no_go
    release.blockers = [b.dict() for b in blockers] # Store blockers in the JSON field
    db.commit()
    db.refresh(release)

    return ReleaseReadinessAnalysis(
        release_id=release.release_id,
        risk_score=risk_score,
        go_no_go_decision=go_no_go,
        summary=summary,
        blockers=blockers
    )


@router.get("/status")
def copilot_status():
    """Check the status of the Copilot endpoints."""
    return {"status": "Copilot is active"}
