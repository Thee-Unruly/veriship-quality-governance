"""Notifications routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import ReleaseApproval, Defect, QAInsight, ApprovalStatus, DefectSeverity, DefectStatus, Release
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


class NotificationItem(BaseModel):
    id: str
    title: str
    description: str
    type: str  # approval, defect, insight
    timestamp: datetime
    link: Optional[str] = None


@router.get("/", response_model=List[NotificationItem])
def get_notifications(db: Session = Depends(get_db)):
    """Get aggregated notifications for the current user context."""
    notifications = []
    
    # 1. Pending Release Approvals
    pending_approvals = (
        db.query(ReleaseApproval)
        .join(Release)
        .filter(ReleaseApproval.status == ApprovalStatus.PENDING)
        .order_by(ReleaseApproval.created_at.desc())
        .limit(5)
        .all()
    )
    
    for approval in pending_approvals:
        notifications.append(NotificationItem(
            id=f"approval-{approval.id}",
            title=f"Release {approval.release.release_id} Pending Approval",
            description=f"Requires review from {approval.approver_role or 'Stakeholder'}",
            type="approval",
            timestamp=approval.created_at,
            link=f"/releases"
        ))
        
    # 2. Critical/High Defects (Open)
    critical_defects = (
        db.query(Defect)
        .filter(
            Defect.status.in_([DefectStatus.OPEN, DefectStatus.REOPENED]),
            Defect.severity.in_([DefectSeverity.CRITICAL, DefectSeverity.HIGH])
        )
        .order_by(Defect.created_at.desc())
        .limit(5)
        .all()
    )
    
    for defect in critical_defects:
        notifications.append(NotificationItem(
            id=f"defect-{defect.id}",
            title=f"New {defect.severity.value.title()} Defect: {defect.defect_id}",
            description=defect.title[:50] + "..." if len(defect.title) > 50 else defect.title,
            type="defect",
            timestamp=defect.created_at,
            link=f"/defects"
        ))

    # 3. Recent AI Insights (last 24 hours)
    recent_insights = (
        db.query(QAInsight)
        .order_by(QAInsight.created_at.desc())
        .limit(3)
        .all()
    )
    
    for insight in recent_insights:
        notifications.append(NotificationItem(
            id=f"insight-{insight.id}",
            title="AI Insight Generated",
            description=insight.title,
            type="insight",
            timestamp=insight.created_at,
            link="/ai-insights"
        ))
        
    # Sort all by timestamp descending
    notifications.sort(key=lambda x: x.timestamp, reverse=True)
    
    return notifications[:10]  # Return top 10
