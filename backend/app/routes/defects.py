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


class DefectUpdate(BaseModel):
    """Defect update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[DefectSeverity] = None
    status: Optional[DefectStatus] = None
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


@router.put("/{defect_id}", response_model=DefectResponse)
def update_defect(
    defect_id: int,
    defect_update: DefectUpdate,
    db: Session = Depends(get_db)
):
    """Update a defect."""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    
    if defect_update.title:
        defect.title = defect_update.title
    if defect_update.description:
        defect.description = defect_update.description
    if defect_update.severity:
        defect.severity = defect_update.severity
    if defect_update.status:
        defect.status = defect_update.status
    if defect_update.found_by:
        defect.found_by = defect_update.found_by
    
    db.commit()
    db.refresh(defect)
    return defect


@router.delete("/{defect_id}")
def delete_defect(defect_id: int, db: Session = Depends(get_db)):
    """Delete a defect."""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    
    db.delete(defect)
    db.commit()
    return {"status": "deleted"}

