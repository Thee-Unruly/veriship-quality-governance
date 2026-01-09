"""Test Case routes."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TestCase, Project
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
    status: Optional[str] = "ongoing"


class TestCaseUpdate(BaseModel):
    """Test case update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[str] = None
    priority: Optional[int] = None
    is_automated: Optional[bool] = None
    status: Optional[str] = None


class TestCaseResponse(BaseModel):
    """Test case response schema."""
    id: int
    project_id: int
    requirement_id: Optional[int] = None
    test_case_id: str
    title: str
    description: Optional[str]
    test_type: str
    priority: int
    coverage_status: float
    is_automated: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BatchTestCaseCreate(BaseModel):
    project_id: int
    requirement_id: Optional[int] = None
    test_cases: List[dict]  # Each dict should match GeneratedTestCase schema


@router.post("/batch-add", response_model=List[TestCaseResponse])
def batch_add_test_cases(batch: BatchTestCaseCreate, db: Session = Depends(get_db)):
    """Batch add test cases (for AI-generated or bulk import)."""
    # Validate that the project exists
    project = db.query(Project).filter(Project.id == batch.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {batch.project_id} not found")
    
    created = []
    for tc in batch.test_cases:
        db_tc = TestCase(
            project_id=batch.project_id,
            requirement_id=batch.requirement_id,
            test_case_id=tc.get("test_case_id") or f"AI-TC-{datetime.utcnow().timestamp()}-{len(created)+1}",
            title=tc["title"],
            description=tc.get("description"),
            test_type=tc.get("test_type", "manual"),
            priority=tc.get("priority", 1),
            test_steps=tc.get("test_steps", []),
            expected_result=tc.get("expected_result", ""),
            status=tc.get("status", "ongoing")
        )
        db.add(db_tc)
        db.commit()
        db.refresh(db_tc)
        created.append(db_tc)
    return created


@router.get("/{project_id}", response_model=List[TestCaseResponse])
def list_test_cases(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """List test cases for a project. Optional `status` filter (ongoing/completed/archived)."""
    query = db.query(TestCase).filter(TestCase.project_id == project_id)
    if status:
        query = query.filter(TestCase.status == status)
    test_cases = query.all()
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
        status=tc.status or "ongoing",
    )
    db.add(db_tc)
    db.commit()
    db.refresh(db_tc)
    return db_tc


@router.put("/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_case_id: int,
    tc_update: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """Update a test case."""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    if tc_update.title:
        test_case.title = tc_update.title
    if tc_update.description:
        test_case.description = tc_update.description
    if tc_update.test_type:
        test_case.test_type = tc_update.test_type
    if tc_update.priority:
        test_case.priority = tc_update.priority
    if tc_update.is_automated is not None:
        test_case.is_automated = tc_update.is_automated
    if tc_update.status is not None:
        test_case.status = tc_update.status
    
    db.commit()
    db.refresh(test_case)
    return test_case


@router.delete("/{test_case_id}")
def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """Delete a test case."""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    db.delete(test_case)
    db.commit()
    return {"status": "deleted"}

