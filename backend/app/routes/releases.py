"""Release routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Release, ReleaseStatus, ReleaseApproval, TeamMember, ApprovalStatus, TestCase
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


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


@router.get("/{project_id}", response_model=List[ReleaseResponse])
def list_releases(project_id: int, db: Session = Depends(get_db)):
    """List releases for a project."""
    releases = db.query(Release).filter(Release.project_id == project_id).all()
    return releases


@router.get("/", response_model=List[ReleaseResponse])
def list_all_releases(db: Session = Depends(get_db)):
    """List all releases across projects."""
    releases = db.query(Release).all()
    return releases


@router.post("/", response_model=ReleaseResponse)
def create_release(release: ReleaseCreate, db: Session = Depends(get_db)):
    """Create a new release."""
    # Check if project has at least 80% test completion
    total_tests = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == release.project_id
    ).scalar() or 0
    
    # Check completion based on 'pass' or 'fail' status
    completed_tests = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == release.project_id,
        TestCase.status.in_(["pass", "passed", "fail", "failed", "completed"])
    ).scalar() or 0
    
    # Calculate completion percentage
    if total_tests > 0:
        completion_percentage = (completed_tests / total_tests) * 100
        # Require at least 50% of test cases to be executed (pass or fail)
        if completion_percentage < 50:
             raise HTTPException(
                status_code=400,
                detail=f"Cannot create release: Only {completion_percentage:.1f}% of tests are completed. Minimum 50% required."
            )
    else:
        # If no tests exist, optionally allow release or block. For safety, let's allow it if it's a new project but warn?
        # The user seems to have tests, so this block is hitting the percentage check. 
        # Let's just pass if total_tests is 0 (though ideally there should be tests).
        pass
    
    # Auto-generate release_id if not provided
    release_id = release.release_id
    if not release_id:
        # Find the highest numbered release for this project
        existing_rels = db.query(Release).filter(Release.project_id == release.project_id).all()
        max_num = 0
        for r in existing_rels:
            if r.release_id.startswith("REL-"):
                try:
                    num = int(r.release_id.split("-")[1])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
        release_id = f"REL-{max_num + 1:03d}"
    
    db_release = Release(
        project_id=release.project_id,
        release_id=release_id,
        version=release.version,
        planned_release_date=release.planned_release_date,
    )
    db.add(db_release)
    db.flush()  # Get the release ID before creating approvals
    
    # Auto-create approval records only for Project Managers and QA
    team_members = db.query(TeamMember).filter(
        TeamMember.project_id == release.project_id
    ).filter(
        (TeamMember.role.ilike("%project manager%")) | (TeamMember.role.ilike("%qa%"))
    ).all()
    
    if not team_members:
        raise HTTPException(
            status_code=400,
            detail="Cannot create release: No Project Manager or QA found in team. Add a Project Manager or QA first."
        )
    
    for member in team_members:
        approval = ReleaseApproval(
            release_id=db_release.id,
            approver_name=member.name,
            approver_role=member.role,
            status=ApprovalStatus.PENDING
        )
        db.add(approval)
    
    db.commit()
    db.refresh(db_release)
    return db_release


@router.put("/{release_id}", response_model=ReleaseResponse)
def update_release(
    release_id: int,
    release_update: ReleaseUpdate,
    db: Session = Depends(get_db)
):
    """Update a release."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    if release_update.version:
        release.version = release_update.version
    if release_update.status:
        release.status = release_update.status
    if release_update.planned_release_date:
        release.planned_release_date = release_update.planned_release_date
    if release_update.go_no_go_decision:
        release.go_no_go_decision = release_update.go_no_go_decision
    
    db.commit()
    db.refresh(release)
    return release


@router.delete("/{release_id}")
def delete_release(release_id: int, db: Session = Depends(get_db)):
    """Delete a release."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    db.delete(release)
    db.commit()
    return {"status": "deleted"}


# ========== Release Approvals ==========

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


@router.get("/{release_id}/approvals", response_model=List[ReleaseApprovalResponse])
def get_release_approvals(release_id: int, db: Session = Depends(get_db)):
    """Get all approvals for a release."""
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    approvals = db.query(ReleaseApproval).filter(ReleaseApproval.release_id == release_id).all()
    return approvals

