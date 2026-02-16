"""API endpoints for the Quality Copilot AI features."""

import json
import time
import requests
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.config import settings
from app.models import Requirement, Release, Defect, DefectStatus, DefectSeverity, Project, CopilotPrompt
from app.schemas.copilot import (
    RequirementClarityAnalysis,
    TestCaseGenerationResult,
    ReleaseReadinessAnalysis,
    BlockingIssue
)
from app.models import QAInsight, Project

router = APIRouter()


def call_openrouter(api_key: str, user_message: str) -> str:
    """Call OpenRouter API with error handling and retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
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
            
            # Handle rate limiting with retry
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limited (429). Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=429,
                        detail="OpenRouter API rate limit exceeded. Please try again in a few moments."
                    )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API error: {response.text}"
                )
            
            return response.json()["choices"][0]["message"]["content"]
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request failed: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to call OpenRouter API after {max_retries} attempts: {str(e)}"
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
        # persist prompt for audit/debug
        try:
            db_prompt = CopilotPrompt(endpoint="analyze_requirement_clarity", prompt_text=prompt)
            db.add(db_prompt)
            db.commit()
            db.refresh(db_prompt)
        except Exception:
            db.rollback()

        # Try the configured clarity key first, then fall back to other OpenRouter keys
        ai_response = None
        last_http_exc = None
        openrouter_keys = [
            settings.openrouter_clarity_api_key,
            settings.openrouter_testcase_api_key,
            settings.openrouter_trial_api_key,
        ]

        for key in openrouter_keys:
            if not key:
                continue
            try:
                ai_response = call_openrouter(key, prompt)
                break
            except HTTPException as e:
                # If it's a rate limit (429), try the next key; otherwise propagate
                if e.status_code == 429:
                    last_http_exc = e
                    continue
                raise

        if ai_response is None:
            if last_http_exc:
                raise last_http_exc
            raise HTTPException(status_code=400, detail="OpenRouter API key not configured or all keys failed.")
        
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
        # persist prompt
        try:
            db_prompt = CopilotPrompt(endpoint="generate_test_cases", prompt_text=prompt)
            db.add(db_prompt)
            db.commit()
            db.refresh(db_prompt)
        except Exception:
            db.rollback()

        if not settings.openrouter_testcase_api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter Test Case API key not configured. Please set OPENROUTER_TESTCASE_API_KEY (or OPENROUTER_API_KEY)."
            )

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
    "/generate-scenarios",
    summary="Generates multiple scenario variants for a test case using AI.",
)
def generate_scenarios(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Generate multiple test scenario variants from a test case + requirement using Gemma via OpenRouter.

    Expects JSON body with keys: `testCase`, `requirement` (optional), `count` (int).
    Returns: { "scenarios": [ ... ] }
    """
    test_case = payload.get("testCase")
    requirement = payload.get("requirement")
    count = int(payload.get("count", 5))

    if not test_case:
        raise HTTPException(status_code=400, detail="Missing testCase in request body")

    # Build a clear prompt asking for JSON output
    prompt = f"""You are a testing assistant. Generate {count} distinct test scenario variants in JSON format.

Given a test case and optional requirement, return exactly {count} different test scenarios.

Format must be:
{{
  "scenarios": [
    {{
      "title": "Scenario title",
      "description": "Brief description",
      "priority": 1,
      "test_type": "Positive|Negative|Edge Case|Performance|Security",
      "steps": [
        {{"type":"http","description":"Step description","method":"GET","url":"/path","expected_status":200}}
      ],
      "expected_result": "Expected outcome"
    }}
  ]
}}

Input Test Case:
{json.dumps(test_case)}

Requirement (if provided):
{json.dumps(requirement)}

Generate exactly {count} distinct scenarios. Return ONLY valid JSON, no extra text."""

    try:
        # Use OpenRouter API key for Gemma model (dedicated trial key for test runner)
        openrouter_key = settings.openrouter_trial_api_key or settings.openrouter_testcase_api_key or settings.openrouter_clarity_api_key
        if not openrouter_key:
            raise HTTPException(status_code=400, detail="OpenRouter API key not configured. Set openrouter_trial_api_key, openrouter_testcase_api_key, or openrouter_clarity_api_key in your .env.")

        ai_text = call_openrouter(openrouter_key, prompt)

        # Extract JSON object from model output
        json_start = ai_text.find('{')
        json_end = ai_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = ai_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = json.loads(ai_text)

        # Expecting a top-level 'scenarios' list
        scenarios = result.get("scenarios") if isinstance(result, dict) else None
        if scenarios is None:
            raise HTTPException(status_code=500, detail="AI did not return scenarios key in JSON")

        return {"scenarios": scenarios}

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call AI provider: {str(e)}")


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
        # persist prompt
        try:
            db_prompt = CopilotPrompt(endpoint="check_release_readiness", prompt_text=prompt)
            db.add(db_prompt)
            db.commit()
            db.refresh(db_prompt)
        except Exception:
            db.rollback()

        if not settings.openrouter_clarity_api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter Clarity API key not configured (used for release checking). Please set OPENROUTER_CLARITY_API_KEY (or OPENROUTER_API_KEY)."
            )

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


@router.post("/apply-insight")
def apply_insight(payload: dict, db: Session = Depends(get_db)):
    """Apply / persist an approved AI insight.

    This endpoint records the approved insight as a `QAInsight` entry for audit
    and potential follow-up automation. It does NOT perform destructive actions
    (e.g., closing defects) — it only records the approval and suggested action.
    """
    title = payload.get("title")
    description = payload.get("description")
    insight_type = payload.get("type") or payload.get("insight_type") or "recommendation"
    action = payload.get("action")
    project_name = payload.get("project")
    project_id = payload.get("project_id")

    # Resolve project_id if only name provided
    if not project_id and project_name:
        proj = db.query(Project).filter(Project.name == project_name).first()
        if proj:
            project_id = proj.id

    # Require a project to store the insight
    if not project_id:
        raise HTTPException(status_code=400, detail="project or project_id required to apply insight")

    qa = QAInsight(
        project_id=project_id,
        insight_type=insight_type,
        title=title,
        description=description,
        confidence_score=payload.get("confidence_score") or 0.0,
        action_items=[action] if action else [],
    )

    db.add(qa)
    db.commit()
    db.refresh(qa)

    return {"status": "applied", "id": qa.id}


# In-memory cache for AI insights (refreshes once per day)
_insights_cache = {
    "data": None,
    "timestamp": None
}
INSIGHTS_CACHE_TTL_SECONDS = 86400  # 24 hours


@router.get("/insights")
def get_ai_insights(db: Session = Depends(get_db)):
    """Return AI-driven or deterministic insights for the dashboard.

    If OpenRouter key is configured, request insights from the LLM. Otherwise
    return deterministic insights computed from DB metrics.
    
    AI insights are cached for 24 hours to preserve API quota.
    """
    global _insights_cache
    
    # Check if we have valid cached AI insights
    now = time.time()
    if _insights_cache["data"] is not None and _insights_cache["timestamp"] is not None:
        age = now - _insights_cache["timestamp"]
        if age < INSIGHTS_CACHE_TTL_SECONDS:
            # Return cached insights (still fresh)
            print(f"[Insights] Returning cached AI insights (age: {int(age)}s, TTL: {INSIGHTS_CACHE_TTL_SECONDS}s)")
            return _insights_cache["data"]
    
    insights = []

    try:
        # Deterministic aggregation function
        def deterministic_insights():
            rows = []
            projects = db.query(Project).all()
            for p in projects:
                ambiguous_count = db.query(Requirement).filter(
                    Requirement.project_id == p.id,
                    Requirement.clarity_score < 50
                ).count()

                coverage_issues = db.query(Release).filter(
                    Release.project_id == p.id,
                    (Release.actual_test_coverage == None) | (Release.actual_test_coverage < 80)
                ).count()

                critical_open = db.query(Defect).filter(
                    Defect.project_id == p.id,
                    Defect.status == DefectStatus.OPEN,
                    Defect.severity == DefectSeverity.CRITICAL
                ).count()

                if ambiguous_count > 0:
                    rows.append({
                        "id": f"req-amb-{p.id}",
                        "type": "warning",
                        "title": "Ambiguous Requirements Detected",
                        "description": f"{ambiguous_count} requirements in {p.name} have low clarity scores and may be non-testable.",
                        "action": "Review Requirements",
                        "project": p.name,
                    })

                if coverage_issues > 0:
                    rows.append({
                        "id": f"cov-gap-{p.id}",
                        "type": "suggestion",
                        "title": "Coverage Gap Identified",
                        "description": f"One or more releases in {p.name} report less than 80% test coverage. Consider adding tests.",
                        "action": "Generate Tests",
                        "project": p.name,
                    })

                if critical_open > 0:
                    rows.append({
                        "id": f"crit-def-{p.id}",
                        "type": "warning",
                        "title": "Critical Defects Open",
                        "description": f"{critical_open} critical open defect(s) in {p.name}. These may block releases.",
                        "project": p.name,
                    })

            # If no insights, provide an info card
            if not rows:
                rows.append({
                    "id": "no-issues",
                    "type": "info",
                    "title": "No immediate AI insights",
                    "description": "Systems look healthy — no glaring issues detected.",
                    "project": "All Projects",
                })

            return rows

        # Prefer LLM if API key present
        if settings.openrouter_clarity_api_key:
            # Build short summary for the model
            proj_summaries = []
            projects = db.query(Project).all()
            for p in projects:
                crit_defs = db.query(Defect).filter(
                    Defect.project_id == p.id,
                    Defect.status == DefectStatus.OPEN,
                    Defect.severity == DefectSeverity.CRITICAL
                ).count()
                low_cov = db.query(Release).filter(
                    Release.project_id == p.id,
                    (Release.actual_test_coverage == None) | (Release.actual_test_coverage < 80)
                ).count()
                amb_reqs = db.query(Requirement).filter(
                    Requirement.project_id == p.id,
                    Requirement.clarity_score < 60
                ).count()

                proj_summaries.append(f"Project {p.name}: {crit_defs} critical defects, {low_cov} releases <80% coverage, {amb_reqs} low-clarity requirements")

            prompt = "Generate a small list (3-6) of actionable AI insights for a dashboard based on these project summaries. Return JSON array with objects having keys: id, type (warning|suggestion|info), title, description, action (optional), project. Only return JSON.\n\n" + "\n".join(proj_summaries)

            # persist prompt for insights
            try:
                db_prompt = CopilotPrompt(endpoint="insights", prompt_text=prompt)
                db.add(db_prompt)
                db.commit()
                db.refresh(db_prompt)
            except Exception:
                db.rollback()

            ai_response = call_openrouter(settings.openrouter_clarity_api_key, prompt)
            # Extract JSON array
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                insights = json.loads(ai_response[json_start:json_end])
                # Cache the AI insights for 24 hours
                _insights_cache["data"] = insights
                _insights_cache["timestamp"] = time.time()
                print(f"[Insights] Cached new AI insights for {INSIGHTS_CACHE_TTL_SECONDS}s")
            else:
                # fallback to deterministic if parsing fails
                insights = deterministic_insights()
        else:
            insights = deterministic_insights()

        return insights

    except Exception:
        # Always return deterministic insights on unexpected errors
        try:
            return deterministic_insights()
        except Exception:
            return []


@router.post("/insights/refresh")
def refresh_ai_insights(db: Session = Depends(get_db)):
    """Force refresh of AI insights cache. Clears the cache and fetches new insights."""
    global _insights_cache
    _insights_cache["data"] = None
    _insights_cache["timestamp"] = None
    print("[Insights] Cache cleared, next request will fetch fresh AI insights")
    return {"status": "cache_cleared", "message": "Next insights request will fetch fresh data from AI"}


@router.get("/prompts/last")
def get_last_prompt(endpoint: str = "insights", db: Session = Depends(get_db)):
    """Return the most recent stored prompt for the given endpoint."""
    p = (
        db.query(CopilotPrompt)
        .filter(CopilotPrompt.endpoint == endpoint)
        .order_by(CopilotPrompt.created_at.desc())
        .first()
    )
    if not p:
        return {"endpoint": endpoint, "prompt_text": None}
    return {"endpoint": p.endpoint, "prompt_text": p.prompt_text, "created_at": p.created_at}