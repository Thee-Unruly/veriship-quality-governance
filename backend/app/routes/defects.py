"""Defect routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Defect, DefectSeverity, DefectStatus, User, UserProjectAssignment
from app.auth import get_current_user
from app.dependencies import assert_project_access, get_user_project_ids
from app.utils import recalculate_project_status
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List

router = APIRouter()

# ========== Schemas ==========

class DefectCreate(BaseModel):
    """Defect creation schema."""
    project_id: int
    defect_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: DefectSeverity = DefectSeverity.MEDIUM
    found_by: Optional[str] = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class DefectUpdate(BaseModel):
    """Defect update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[DefectSeverity] = None
    status: Optional[DefectStatus] = None
    found_by: Optional[str] = None

    @field_validator("severity", "status", mode="before")
    @classmethod
    def normalize_enums(cls, v):
        if isinstance(v, str):
            return v.lower().replace(" ", "_").replace("-", "_")
        return v


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


# ========== Defect Endpoints ==========

@router.get("/all", response_model=List[DefectResponse])
def list_all_defects(
    severity: Optional[DefectSeverity] = None,
    status: Optional[DefectStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all defects across every project the user belongs to."""
    user_project_ids = get_user_project_ids(db, current_user.id)
    
    query = db.query(Defect).filter(Defect.project_id.in_(user_project_ids))
    
    if severity:
        query = query.filter(Defect.severity == severity)
    if status:
        query = query.filter(Defect.status == status)
        
    return query.order_by(Defect.created_at.desc()).all()


@router.get("/{project_id}", response_model=List[DefectResponse])
def list_defects(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """List defects for a specific project if authorized."""
    assert_project_access(db, project_id, current_user.id)
    
    defects = db.query(Defect).filter(Defect.project_id == project_id).all()
    return defects


@router.post("/", response_model=DefectResponse)
def create_defect(
    defect: DefectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new defect for an authorized project."""
    assert_project_access(db, defect.project_id, current_user.id)

    # Auto-generate defect_id if not provided
    defect_id = defect.defect_id
    if not defect_id:
        existing_defs = db.query(Defect).filter(Defect.project_id == defect.project_id).all()
        max_num = 0
        for d in existing_defs:
            if d.defect_id and d.defect_id.startswith("DEF-"):
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
    
    try:
        recalculate_project_status(db, db_defect.project_id)
    except Exception:
        pass
        
    return db_defect


@router.put("/{defect_id}", response_model=DefectResponse)
def update_defect(
    defect_id: int,
    defect_update: DefectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a defect if the user owns the parent project."""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    
    assert_project_access(db, defect.project_id, current_user.id)
    
    if defect_update.title is not None:
        defect.title = defect_update.title
    if defect_update.description is not None:
        defect.description = defect_update.description
    if defect_update.severity is not None:
        defect.severity = defect_update.severity
    if defect_update.status is not None:
        defect.status = defect_update.status
    if defect_update.found_by is not None:
        defect.found_by = defect_update.found_by
    
    db.commit()
    db.refresh(defect)
    
    try:
        recalculate_project_status(db, defect.project_id)
    except Exception:
        pass
        
    return defect


@router.delete("/{defect_id}")
def delete_defect(
    defect_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a defect if the user owns the parent project."""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    
    assert_project_access(db, defect.project_id, current_user.id)
    
    project_id = defect.project_id
    db.delete(defect)
    db.commit()
    
    try:
        recalculate_project_status(db, project_id)
    except Exception:
        pass
        
    return {"status": "deleted"}