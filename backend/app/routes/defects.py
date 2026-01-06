"""Defect routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Defect, DefectSeverity, DefectStatus
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class DefectCreate(BaseModel):
    """Defect creation schema."""
    project_id: int
    defect_id: str
    title: str
    description: Optional[str] = None
    severity: DefectSeverity = DefectSeverity.MEDIUM
    found_by: Optional[str] = None


class DefectResponse(BaseModel):
    """Defect response schema."""
    id: int
    project_id: int
    defect_id: str
    title: str
    severity: DefectSeverity
    status: DefectStatus
    release_risk_score: float
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{project_id}", response_model=List[DefectResponse])
def list_defects(project_id: int, db: Session = Depends(get_db)):
    """List defects for a project."""
    defects = db.query(Defect).filter(Defect.project_id == project_id).all()
    return defects


@router.post("/", response_model=DefectResponse)
def create_defect(defect: DefectCreate, db: Session = Depends(get_db)):
    """Create a new defect."""
    db_defect = Defect(
        project_id=defect.project_id,
        defect_id=defect.defect_id,
        title=defect.title,
        description=defect.description,
        severity=defect.severity,
        found_by=defect.found_by,
    )
    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)
    return db_defect
