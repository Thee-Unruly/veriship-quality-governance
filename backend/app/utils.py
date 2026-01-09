"""Utility helpers for backend operations."""
from sqlalchemy.orm import Session
from app.models import Project, Defect, DefectSeverity, DefectStatus, ProjectStatus
from datetime import datetime


def recalculate_project_status(db: Session, project_id: int) -> None:
    """Recalculate and persist the project's status based on defect counts.

    Rules (simple heuristic):
    - If any OPEN CRITICAL defects -> AT_RISK
    - If 3 or more OPEN HIGH defects -> AT_RISK
    - If no OPEN defects -> ON_TRACK
    - Otherwise leave as IN_PROGRESS/ON_TRACK depending on previous value
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return

    critical_open = (
        db.query(Defect)
        .filter(
            Defect.project_id == project_id,
            Defect.status == DefectStatus.OPEN,
            Defect.severity == DefectSeverity.CRITICAL,
        )
        .count()
    )

    high_open = (
        db.query(Defect)
        .filter(
            Defect.project_id == project_id,
            Defect.status == DefectStatus.OPEN,
            Defect.severity == DefectSeverity.HIGH,
        )
        .count()
    )

    open_total = (
        db.query(Defect)
        .filter(Defect.project_id == project_id, Defect.status == DefectStatus.OPEN)
        .count()
    )

    new_status = project.status

    if critical_open > 0:
        new_status = ProjectStatus.AT_RISK
    elif high_open >= 3:
        new_status = ProjectStatus.AT_RISK
    elif open_total == 0:
        new_status = ProjectStatus.ON_TRACK
    else:
        # keep current status if it's a more specific state
        if project.status in (ProjectStatus.PLANNING, ProjectStatus.COMPLETED, ProjectStatus.BLOCKED):
            new_status = project.status
        else:
            new_status = ProjectStatus.IN_PROGRESS

    if new_status != project.status:
        project.status = new_status
        project.updated_at = datetime.utcnow()
        db.commit()
