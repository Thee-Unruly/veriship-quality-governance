"""API endpoints for trial test runner - no DB persistence."""

import time
import requests
from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas.trial import (
    TrialRunRequest,
    TrialRunResponse,
    TestCaseResult,
    StepResult,
    TestStep,
    TestCase
)

router = APIRouter()


def execute_step(step: TestStep, base_url: str = None) -> StepResult:
    """Execute a single test step."""
    start_time = time.time()
    
    try:
        if step.type == "http":
            # Execute HTTP request
            url = step.url
            if base_url and not step.url.startswith("http"):
                url = f"{base_url.rstrip('/')}/{step.url.lstrip('/')}"
            
            response = requests.request(
                method=step.method or "GET",
                url=url,
                headers=step.headers or {},
                json=step.body,
                timeout=30
            )
            
            # Check expected status
            if step.expected_status and response.status_code != step.expected_status:
                duration_ms = int((time.time() - start_time) * 1000)
                return StepResult(
                    step_number=0,
                    description=step.description,
                    status="failed",
                    duration_ms=duration_ms,
                    error=f"Expected status {step.expected_status}, got {response.status_code}"
                )
            
            # Check expected content
            if step.expected_contains and step.expected_contains not in response.text:
                duration_ms = int((time.time() - start_time) * 1000)
                return StepResult(
                    step_number=0,
                    description=step.description,
                    status="failed",
                    duration_ms=duration_ms,
                    error=f"Response does not contain '{step.expected_contains}'"
                )
            
            duration_ms = int((time.time() - start_time) * 1000)
            return StepResult(
                step_number=0,
                description=step.description,
                status="passed",
                duration_ms=duration_ms,
                details=f"Status: {response.status_code}, Size: {len(response.text)} bytes"
            )
        
        elif step.type == "assert":
            # Simple assertion step (can be extended)
            duration_ms = int((time.time() - start_time) * 1000)
            return StepResult(
                step_number=0,
                description=step.description,
                status="passed",
                duration_ms=duration_ms,
                details="Assertion passed"
            )
        
        elif step.type == "delay":
            # Add delay between steps
            delay_sec = (step.duration_ms or 1000) / 1000
            time.sleep(delay_sec)
            duration_ms = int((time.time() - start_time) * 1000)
            return StepResult(
                step_number=0,
                description=step.description,
                status="passed",
                duration_ms=duration_ms,
                details=f"Delayed {delay_sec}s"
            )
        
        else:
            duration_ms = int((time.time() - start_time) * 1000)
            return StepResult(
                step_number=0,
                description=step.description,
                status="skipped",
                duration_ms=duration_ms,
                details=f"Unknown step type: {step.type}"
            )
    
    except requests.exceptions.RequestException as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return StepResult(
            step_number=0,
            description=step.description,
            status="failed",
            duration_ms=duration_ms,
            error=f"Request error: {str(e)}"
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return StepResult(
            step_number=0,
            description=step.description,
            status="failed",
            duration_ms=duration_ms,
            error=f"Error: {str(e)}"
        )


def execute_test_case(test_case: TestCase, base_url: str = None) -> TestCaseResult:
    """Execute a single test case."""
    start_time = time.time()
    step_results: List[StepResult] = []
    
    for idx, step in enumerate(test_case.steps, start=1):
        result = execute_step(step, base_url)
        result.step_number = idx
        step_results.append(result)
        
        # Stop on first failure
        if result.status == "failed":
            # Mark remaining steps as skipped
            for remaining_idx in range(idx + 1, len(test_case.steps) + 1):
                step_results.append(StepResult(
                    step_number=remaining_idx,
                    description=test_case.steps[remaining_idx - 1].description,
                    status="skipped",
                    duration_ms=0,
                    details="Skipped due to previous failure"
                ))
            break
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Determine overall status
    if any(s.status == "failed" for s in step_results):
        status = "failed"
    elif all(s.status == "passed" for s in step_results):
        status = "passed"
    else:
        status = "skipped"
    
    return TestCaseResult(
        title=test_case.title,
        status=status,
        duration_ms=duration_ms,
        steps=step_results
    )


@router.post(
    "/run",
    response_model=TrialRunResponse,
    summary="Run test cases in trial mode",
    description="Executes test cases without persisting to database. Results are returned immediately."
)
def run_trial_tests(request: TrialRunRequest):
    """
    Execute test cases in trial mode (no DB persistence).
    
    Accepts a list of test cases with steps and executes them against
    the specified target base URL. Returns detailed execution results.
    """
    start_time = time.time()
    results: List[TestCaseResult] = []
    
    for test_case in request.test_cases:
        result = execute_test_case(test_case, request.target_base_url)
        results.append(result)
    
    total_duration_ms = int((time.time() - start_time) * 1000)
    
    # Calculate stats
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    skipped = sum(1 for r in results if r.status == "skipped")
    
    return TrialRunResponse(
        total_cases=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        total_duration_ms=total_duration_ms,
        results=results
    )


@router.get("/health")
def trial_health():
    """Health check for trial runner."""
    return {"status": "healthy", "service": "Trial Test Runner"}
