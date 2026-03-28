"""Release routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import (
    Release, 
    ReleaseStatus, 
    ReleaseApproval, 
    TeamMember, 
    ApprovalStatus, 
    TestCase, 
    User, 
    UserProjectAssignment
)
from app.routes.auth import get_current_user
from app.dependencies import assert_project_access, get_user_project_ids
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List

router = APIRouter()

# ========== Schemas ==========

class ReleaseCreate(BaseModel):
    """Release creation schema."""
    project_id: int
    release_id: Optional[str] = None
    version: str
    planned_release_date: Optional[datetime] = None


class ReleaseUpdate(BaseModel):
    """Release update schema."""
    version: Optional[str] = None
    status: Optional[ReleaseStatus] = None
    planned_release_date: Optional[datetime] = None
    go_no_go_decision: Optional[str] = None


class ReleaseResponse(BaseModel):
    """Release response schema."""
    id: int
    project_id: int
    release_id: str
    version: str
    status: ReleaseStatus
    risk_score: float
    go_no_go_decision: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReleaseApprovalResponse(BaseModel):
    """Release approval response schema."""
    id: int
    release_id: int
    approver_name: str
    approver_role: Optional[str]
    status: str
    comments: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ReleaseApproveRequest(BaseModel):
    """Payload for approving or rejecting a release."""
    approver_name: str
    decision: str 
    comments: Optional[str] = None


# ========== Release Endpoints ==========

@router.get("/{project_id}", response_model=List[ReleaseResponse])
def list_releases(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """List releases for a project if authorized."""
    assert_project_access(db, project_id, current_user.id)
    releases = db.query(Release).filter(Release.project_id == project_id).all()
    return releases


@router.get("/", response_model=List[ReleaseResponse])
def list_all_releases(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """List all releases across projects assigned to the user."""
    user_project_ids = get_user_project_ids(db, current_user.id)
    
    releases = db.query(Release).filter(Release.project_id.in_(user_project_ids)).all()
    return releases


@router.post("/", response_model=ReleaseResponse)
def create_release(
    release: ReleaseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new release for an authorized project."""
    assert_project_access(db, release.project_id, current_user.id)
    
    # Test completion check
    total_tests = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == release.project_id
    ).scalar() or 0
    
    completed_tests = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == release.project_id,
        TestCase.status.in_(["pass", "passed", "fail", "failed", "completed"])
    ).scalar() or 0
    
    if total_tests > 0:
        completion_percentage = (completed_tests / total_tests) * 100
        if completion_percentage < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create release: Only {completion_percentage:.1f}% of tests are completed. Minimum 50% required."
            )
    
    # Auto-generate release_id if not provided
    release_id = release.release_id
    if not release_id:
        existing_rels = db.query(Release).filter(Release.project_id == release.project_id).all()
        max_num = max(
            [int(r.release_id.split("-")[1]) for r in existing_rels 
             if r.release_id and r.release_id.startswith("REL-")] + [0]
        )
        release_id = f"REL-{max_num + 1:03d}"
    
    db_release = Release(
        project_id=release.project_id,
        release_id=release_id,
        version=release.version,
        planned_release_date=release.planned_release_date,
    )
    db.add(db_release)
    db.flush() 
    
    # Auto-create approval records for Project Manager and QA roles
    team_members = db.query(TeamMember).filter(
        TeamMember.project_id == release.project_id,
        (TeamMember.role.ilike("%project manager%")) | (TeamMember.role.ilike("%qa%"))
    ).all()
    
    if not team_members:
        raise HTTPException(
            status_code=400,
            detail="Cannot create release: No Project Manager or QA found in team."
        )
    
    for member in team_members:
        db.add(ReleaseApproval(
            release_id=db_release.id,
            approver_name=member.name,
            approver_role=member.role,
            status=ApprovalStatus.PENDING
        ))
    
    db.commit()
    db.refresh(db_release)
    return db_release


@router.put("/{release_id}", response_model=ReleaseResponse)
def update_release(
    release_id: int,
    release_update: ReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a release if authorized."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    assert_project_access(db, release.project_id, current_user.id)
    
    if release_update.version is not None:
        release.version = release_update.version
    if release_update.status is not None:
        release.status = release_update.status
    if release_update.planned_release_date is not None:
        release.planned_release_date = release_update.planned_release_date
    if release_update.go_no_go_decision is not None:
        release.go_no_go_decision = release_update.go_no_go_decision
    
    db.commit()
    db.refresh(release)
    return release


@router.delete("/{release_id}")
def delete_release(
    release_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a release if authorized."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    assert_project_access(db, release.project_id, current_user.id)
    
    db.delete(release)
    db.commit()
    return {"status": "deleted"}


# ========== Release Approvals ==========

@router.get("/{release_id}/approvals", response_model=List[ReleaseApprovalResponse])
def get_release_approvals(
    release_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get all approvals for a release if authorized."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    assert_project_access(db, release.project_id, current_user.id)
    
    approvals = db.query(ReleaseApproval).filter(ReleaseApproval.release_id == release_id).all()
    return approvals


@router.post("/{release_id}/approve", response_model=ReleaseApprovalResponse)
def approve_release(
    release_id: int,
    payload: ReleaseApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a release if authorized."""
    decision = payload.decision.lower()
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    assert_project_access(db, release.project_id, current_user.id)

    approval = db.query(ReleaseApproval).filter(
        ReleaseApproval.release_id == release_id,
        ReleaseApproval.approver_name == payload.approver_name,
        ReleaseApproval.status == ApprovalStatus.PENDING,
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="No pending approval found for this approver.")

    approval.status = ApprovalStatus.APPROVED if decision == "approved" else ApprovalStatus.REJECTED
    approval.comments = payload.comments
    approval.approved_at = datetime.now(timezone.utc)

    # Update release status based on all approvals
    all_approvals = db.query(ReleaseApproval).filter(ReleaseApproval.release_id == release_id).all()
    pending_count = sum(1 for a in all_approvals if a.status == ApprovalStatus.PENDING)
    rejected_count = sum(1 for a in all_approvals if a.status == ApprovalStatus.REJECTED)

    if pending_count == 0:
        if rejected_count > 0:
            release.go_no_go_decision = "rejected"
            release.status = ReleaseStatus.BLOCKED
        else:
            release.go_no_go_decision = "approved"
            release.status = ReleaseStatus.RELEASED

    db.commit()
    db.refresh(approval)
    return approval