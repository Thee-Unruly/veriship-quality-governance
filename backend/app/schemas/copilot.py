"""Pydantic schemas for Quality Copilot features."""
from pydantic import BaseModel, Field
from typing import List, Optional

class RequirementClarityInput(BaseModel):
    """Schema for the input to the requirement clarity analyzer."""
    requirement_text: str = Field(..., min_length=20, description="The full text of the requirement to be analyzed.")

class RequirementClarityAnalysis(BaseModel):
    """Schema for the output of the requirement clarity analysis."""
    clarity_score: float = Field(..., ge=0, le=100, description="The clarity score from 0 to 100.")
    is_testable: bool = Field(..., description="Whether the requirement is considered testable.")
    ambiguous_terms: List[str] = Field(..., description="A list of ambiguous terms found in the requirement.")
    missing_criteria: List[str] = Field(..., description="A list of suggested criteria that might be missing.")
    suggestions: List[str] = Field(..., description="General suggestions for improving the requirement.")

    class Config:
        orm_mode = True


# Schemas for Test Case Generation
class GeneratedTestCase(BaseModel):
    """Schema for a single AI-generated test case suggestion."""
    title: str = Field(..., description="The title of the test case.")
    description: Optional[str] = Field(None, description="A brief description of the test case's purpose.")
    test_type: str = Field(..., description="Type of test (e.g., 'Positive', 'Negative', 'Edge Case', 'Performance').")
    priority: int = Field(..., ge=1, le=5, description="Suggested priority from 1 (High) to 5 (Low).")
    test_steps: List[str] = Field(..., description="A list of steps to execute the manual test.")
    expected_result: str = Field(..., description="The expected outcome of the test.")

class TestCaseGenerationResult(BaseModel):
    """Schema for the result of a test case generation request."""
    generated_test_cases: List[GeneratedTestCase]

    class Config:
        orm_mode = True


# Schemas for Release Readiness
class BlockingIssue(BaseModel):
    """Schema for a single issue that might block a release."""
    issue_type: str = Field(..., description="Type of issue (e.g., 'Defect', 'Requirement').")
    identifier: str = Field(..., description="The unique ID of the issue (e.g., 'DEF-001', 'REQ-123').")
    title: str = Field(..., description="The title of the issue.")
    status: str = Field(..., description="The current status of the issue.")
    severity: Optional[str] = Field(None, description="The severity, if applicable (e.g., 'Critical').")

class ReleaseReadinessAnalysis(BaseModel):
    """Schema for the comprehensive release readiness analysis."""
    release_id: str
    risk_score: float = Field(..., ge=0, le=100)
    go_no_go_decision: str = Field(..., description="The final 'GO', 'NO-GO', or 'CONDITIONAL' recommendation.")
    summary: str
    blockers: List[BlockingIssue]

    class Config:
        orm_mode = True
