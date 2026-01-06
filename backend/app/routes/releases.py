"""Release routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Release, ReleaseStatus
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class ReleaseCreate(BaseModel):
    """Release creation schema."""
    project_id: int
    release_id: str
    version: str
    planned_release_date: Optional[datetime] = None


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


@router.post("/", response_model=ReleaseResponse)
def create_release(release: ReleaseCreate, db: Session = Depends(get_db)):
    """Create a new release."""
    db_release = Release(
        project_id=release.project_id,
        release_id=release.release_id,
        version=release.version,
        planned_release_date=release.planned_release_date,
    )
    db.add(db_release)
    db.commit()
    db.refresh(db_release)
    return db_release
