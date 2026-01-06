"""Test Case routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TestCase
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class TestCaseCreate(BaseModel):
    """Test case creation schema."""
    project_id: int
    requirement_id: Optional[int] = None
    test_case_id: str
    title: str
    description: Optional[str] = None
    test_type: str = "manual"
    priority: Optional[int] = 1


class TestCaseResponse(BaseModel):
    """Test case response schema."""
    id: int
    project_id: int
    test_case_id: str
    title: str
    description: Optional[str]
    test_type: str
    priority: int
    coverage_status: float
    is_automated: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{project_id}", response_model=List[TestCaseResponse])
def list_test_cases(project_id: int, db: Session = Depends(get_db)):
    """List test cases for a project."""
    test_cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()
    return test_cases


@router.post("/", response_model=TestCaseResponse)
def create_test_case(tc: TestCaseCreate, db: Session = Depends(get_db)):
    """Create a new test case."""
    db_tc = TestCase(
        project_id=tc.project_id,
        requirement_id=tc.requirement_id,
        test_case_id=tc.test_case_id,
        title=tc.title,
        description=tc.description,
        test_type=tc.test_type,
        priority=tc.priority,
    )
    db.add(db_tc)
    db.commit()
    db.refresh(db_tc)
    return db_tc
