"""Schemas for trial test runner."""

from pydantic import BaseModel
from typing import List, Optional, Literal


class TestStep(BaseModel):
    """A single test step."""
    type: Literal["http", "assert", "delay"]
    description: str
    # For HTTP requests
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None
    # For assertions
    expected_status: Optional[int] = None
    expected_contains: Optional[str] = None
    # For delays
    duration_ms: Optional[int] = None


class TestCase(BaseModel):
    """A single test case to execute."""
    title: str
    description: str
    test_type: str
    priority: int
    steps: List[TestStep]
    expected_result: str


class TrialRunRequest(BaseModel):
    """Request to run test cases."""
    test_cases: List[TestCase]
    target_base_url: Optional[str] = None


class StepResult(BaseModel):
    """Result of a single step execution."""
    step_number: int
    description: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: int
    details: Optional[str] = None
    error: Optional[str] = None


class TestCaseResult(BaseModel):
    """Result of a single test case execution."""
    title: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: int
    steps: List[StepResult]
    error: Optional[str] = None


class TrialRunResponse(BaseModel):
    """Response from a trial run."""
    total_cases: int
    passed: int
    failed: int
    skipped: int
    total_duration_ms: int
    results: List[TestCaseResult]
