"""Requirement routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Requirement, RequirementStatus
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class RequirementCreate(BaseModel):
    """Requirement creation schema."""
    project_id: int
    requirement_id: str
    title: str
    description: str
    acceptance_criteria: Optional[List[str]] = []
    priority: Optional[int] = 1


class RequirementResponse(BaseModel):
    """Requirement response schema."""
    id: int
    project_id: int
    requirement_id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    status: RequirementStatus
    clarity_score: float
    is_testable: bool
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{project_id}", response_model=List[RequirementResponse])
def list_requirements(project_id: int, db: Session = Depends(get_db)):
    """List requirements for a project."""
    requirements = db.query(Requirement).filter(Requirement.project_id == project_id).all()
    return requirements


@router.post("/", response_model=RequirementResponse)
def create_requirement(req: RequirementCreate, db: Session = Depends(get_db)):
    """Create a new requirement."""
    db_req = Requirement(
        project_id=req.project_id,
        requirement_id=req.requirement_id,
        title=req.title,
        description=req.description,
        acceptance_criteria=req.acceptance_criteria or [],
        priority=req.priority,
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req
