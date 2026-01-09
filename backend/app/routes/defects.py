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
    defect_id: Optional[str] = None
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
    description: Optional[str] = None
    title: str
    severity: DefectSeverity
    status: DefectStatus
    release_risk_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{project_id}", response_model=List[DefectResponse])
def list_defects(project_id: int, db: Session = Depends(get_db)):
    """List defects for a project."""
    defects = db.query(Defect).filter(Defect.project_id == project_id).all()
    return defects


@router.post("/", response_model=DefectResponse)
def create_defect(defect: DefectCreate, db: Session = Depends(get_db)):
    """Create a new defect."""
    # Auto-generate defect_id if not provided
    defect_id = defect.defect_id
    if not defect_id:
        # Find the highest numbered defect for this project
        existing_defs = db.query(Defect).filter(Defect.project_id == defect.project_id).all()
        max_num = 0
        for d in existing_defs:
            if d.defect_id.startswith("DEF-"):
                try:
                    num = int(d.defect_id.split("-")[1])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
        defect_id = f"DEF-{max_num + 1:03d}"
    
    db_defect = Defect(
        project_id=defect.project_id,
        defect_id=defect_id,
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

