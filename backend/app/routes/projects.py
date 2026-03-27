"""Project routes."""
from app.auth import get_current_user
from app.models import User
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
    TeamMember,
)
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List

router = APIRouter()

# ========== Schemas ==========

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

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower().replace(" ", "-").replace("_", "-")
        return v

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

class TeamMemberCreate(BaseModel):
    """Team member creation schema."""
    name: str
    email: Optional[str] = None
    role: Optional[str] = "Member"

class TeamMemberResponse(BaseModel):
    """Team member response schema."""
    id: int
    project_id: int
    name: str
    email: Optional[str]
    role: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ========== Project Endpoints ==========

@router.get("/", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List only projects assigned to the current user."""
    projects = db.query(Project).join(UserProjectAssignment).filter(
        UserProjectAssignment.user_id == current_user.id
    ).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get a specific project if the user is authorized."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Ownership Check
    if not db.query(UserProjectAssignment).filter_by(project_id=project_id, user_id=current_user.id).first():
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return project

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new project and assign it to the creator."""
    db_project = Project(
        name=project.name,
        description=project.description,
        target_release_date=project.target_release_date,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Assign project to the user who created it
    assignment = UserProjectAssignment(user_id=current_user.id, project_id=db_project.id)
    db.add(assignment)
    db.commit()
    
    return db_project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project if the user is authorized."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Ownership Check
    if not db.query(UserProjectAssignment).filter_by(project_id=project_id, user_id=current_user.id).first():
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a project and all related records if the user is authorized."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Ownership Check
    if not db.query(UserProjectAssignment).filter_by(project_id=project_id, user_id=current_user.id).first():
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        db.query(UserProjectAssignment).filter(UserProjectAssignment.project_id == project_id).delete(synchronize_session=False)
        db.query(QualityMetric).filter(QualityMetric.project_id == project_id).delete(synchronize_session=False)
        db.query(CI_CDPipeline).filter(CI_CDPipeline.project_id == project_id).delete(synchronize_session=False)
        db.query(ProductionIssue).filter(ProductionIssue.project_id == project_id).delete(synchronize_session=False)
        db.query(QAInsight).filter(QAInsight.project_id == project_id).delete(synchronize_session=False)

        db.delete(project)
        db.commit()
        return {"status": "deleted"}
    except Exception as e:
        db.rollback()
        # Log error logic remains the same
        raise HTTPException(status_code=500, detail="Server error during deletion")

# ========== Team Member Endpoints ==========

@router.get("/{project_id}/team", response_model=List[TeamMemberResponse])
def get_project_team(project_id: int, db: Session = Depends(get_db)):
    """Get all team members for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team_members = db.query(TeamMember).filter(TeamMember.project_id == project_id).all()
    return team_members

@router.post("/{project_id}/team", response_model=TeamMemberResponse)
def add_team_member(project_id: int, member: TeamMemberCreate, db: Session = Depends(get_db)):
    """Add a team member to a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_member = TeamMember(
        project_id=project_id,
        name=member.name,
        email=member.email,
        role=member.role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@router.put("/{project_id}/team/{member_id}", response_model=TeamMemberResponse)
def update_team_member(project_id: int, member_id: int, member_update: TeamMemberCreate, db: Session = Depends(get_db)):
    """Update a team member."""
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.project_id == project_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    if member_update.name: member.name = member_update.name
    if member_update.email: member.email = member_update.email
    if member_update.role: member.role = member_update.role
    
    db.commit()
    db.refresh(member)
    return member

@router.delete("/{project_id}/team/{member_id}")
def remove_team_member(project_id: int, member_id: int, db: Session = Depends(get_db)):
    """Remove a team member from a project."""
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.project_id == project_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    db.delete(member)
    db.commit()
    return {"status": "deleted"}