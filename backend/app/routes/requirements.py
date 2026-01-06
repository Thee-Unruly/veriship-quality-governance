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


class RequirementUpdate(BaseModel):
    """Requirement update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    status: Optional[RequirementStatus] = None
    priority: Optional[int] = None


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


@router.put("/{requirement_id}", response_model=RequirementResponse)
def update_requirement(
    requirement_id: int,
    req_update: RequirementUpdate,
    db: Session = Depends(get_db)
):
    """Update a requirement."""
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if req_update.title:
        requirement.title = req_update.title
    if req_update.description:
        requirement.description = req_update.description
    if req_update.acceptance_criteria:
        requirement.acceptance_criteria = req_update.acceptance_criteria
    if req_update.status:
        requirement.status = req_update.status
    if req_update.priority:
        requirement.priority = req_update.priority
    
    db.commit()
    db.refresh(requirement)
    return requirement


@router.delete("/{requirement_id}")
def delete_requirement(requirement_id: int, db: Session = Depends(get_db)):
    """Delete a requirement."""
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    db.delete(requirement)
    db.commit()
    return {"status": "deleted"}

