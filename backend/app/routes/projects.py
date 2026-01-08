"""Project routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Project,
    ProjectStatus,
    UserProjectAssignment,
    QualityMetric,
    CI_CDPipeline,
    ProductionIssue,
    QAInsight,
)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class ProjectCreate(BaseModel):
    """Project creation schema."""
    name: str
    description: Optional[str] = None
    target_release_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """Project update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    target_release_date: Optional[datetime] = None


class ProjectResponse(BaseModel):
    """Project response schema."""
    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    start_date: datetime
    target_release_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """List all projects."""
    projects = db.query(Project).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    db_project = Project(
        name=project.name,
        description=project.description,
        target_release_date=project.target_release_date,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_update.name:
        project.name = project_update.name
    if project_update.description:
        project.description = project_update.description
    if project_update.status:
        project.status = project_update.status
    if project_update.target_release_date:
        project.target_release_date = project_update.target_release_date
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        # Delete related rows that are not configured with ORM cascade
        db.query(UserProjectAssignment).filter(UserProjectAssignment.project_id == project_id).delete(synchronize_session=False)
        db.query(QualityMetric).filter(QualityMetric.project_id == project_id).delete(synchronize_session=False)
        db.query(CI_CDPipeline).filter(CI_CDPipeline.project_id == project_id).delete(synchronize_session=False)
        db.query(ProductionIssue).filter(ProductionIssue.project_id == project_id).delete(synchronize_session=False)
        db.query(QAInsight).filter(QAInsight.project_id == project_id).delete(synchronize_session=False)

        db.delete(project)
        db.commit()
        return {"status": "deleted"}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            with open("c:/Users/ibrahim.fadhili/Videos/VeriShip/veriship-quality-governance/backend/delete_error.log", "a", encoding="utf-8") as f:
                f.write(f"Project delete failed for id={project_id}\n")
                f.write(tb + "\n")
        except Exception:
            pass
        db.rollback()
        raise HTTPException(status_code=500, detail="Server error, check backend/delete_error.log")
