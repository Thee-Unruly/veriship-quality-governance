"""Metrics and analytics routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import (
    Project,
    Requirement,
    TestCase,
    Defect,
    Release,
    TestExecution,
    TestStatus,
    DefectStatus,
    DefectSeverity,
)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models import QualityMetric

router = APIRouter()


class MetricsResponse(BaseModel):
    """Metrics response schema."""
    total_requirements: int
    total_test_cases: int
    total_defects: int
    open_defects: int
    critical_defects: int
    test_pass_rate: float
    pending_releases: int
    overall_risk_score: float
    coverage_percent: float


class ProjectMetrics(BaseModel):
    """Per-project metrics."""
    project_id: int
    project_name: str
    requirements_count: int
    test_cases_count: int
    defects_open: int
    defects_critical: int
    risk_score: float
    coverage_percent: float


class ActivityLog(BaseModel):
    """Activity log entry."""
    id: int
    timestamp: datetime
    activity_type: str
    description: str
    project_name: Optional[str]


@router.get("/dashboard", response_model=MetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get aggregated metrics for dashboard."""
    # Count total requirements
    total_requirements = db.query(func.count(Requirement.id)).scalar() or 0
    
    # Count total test cases
    total_test_cases = db.query(func.count(TestCase.id)).scalar() or 0
    
    # Count defects
    total_defects = db.query(func.count(Defect.id)).scalar() or 0
    open_defects = (
        db.query(func.count(Defect.id))
        .filter(Defect.status.in_([DefectStatus.OPEN, DefectStatus.IN_PROGRESS]))
        .scalar()
        or 0
    )
    critical_defects = (
        db.query(func.count(Defect.id))
        .filter(Defect.severity.in_([DefectSeverity.CRITICAL, DefectSeverity.HIGH]))
        .scalar()
        or 0
    )
    
    # Calculate test pass rate
    passed_tests = (
        db.query(func.count(TestExecution.id))
        .filter(TestExecution.status == TestStatus.PASSED)
        .scalar()
        or 0
    )
    total_executions = db.query(func.count(TestExecution.id)).scalar() or 1
    test_pass_rate = (passed_tests / total_executions * 100) if total_executions > 0 else 0
    
    # Count pending releases
    pending_releases = (
        db.query(func.count(Release.id))
        .filter(Release.status != "released")
        .scalar()
        or 0
    )
    
    # Calculate overall risk score (0-100)
    # Based on: defect density (40%), test coverage (30%), release readiness (30%)
    active_projects = db.query(func.count(Project.id)).scalar() or 1
    defect_density_score = min(100, (open_defects / max(1, total_test_cases)) * 100)
    coverage_score = max(0, 100 - (total_defects / max(1, total_requirements) * 50))
    
    overall_risk = (defect_density_score * 0.4) + ((100 - coverage_score) * 0.3) + (
        (critical_defects / max(1, total_defects) * 100 if total_defects > 0 else 0) * 0.3
    )
    
    return MetricsResponse(
        total_requirements=total_requirements,
        total_test_cases=total_test_cases,
        total_defects=total_defects,
        open_defects=open_defects,
        critical_defects=critical_defects,
        test_pass_rate=round(test_pass_rate, 1),
        pending_releases=pending_releases,
        overall_risk_score=round(min(100, max(0, overall_risk)), 1),
        coverage_percent=round(coverage_score, 1),
    )


@router.get("/projects", response_model=List[ProjectMetrics])
def get_project_metrics(db: Session = Depends(get_db)):
    """Get metrics for each project."""
    projects = db.query(Project).all()
    metrics = []
    
    for project in projects:
        req_count = db.query(func.count(Requirement.id)).filter(
            Requirement.project_id == project.id
        ).scalar() or 0
        
        tc_count = db.query(func.count(TestCase.id)).filter(
            TestCase.project_id == project.id
        ).scalar() or 0
        
        open_defects = (
            db.query(func.count(Defect.id))
            .filter(
                Defect.project_id == project.id,
                Defect.status.in_([DefectStatus.OPEN, DefectStatus.IN_PROGRESS])
            )
            .scalar()
            or 0
        )
        
        critical_def = (
            db.query(func.count(Defect.id))
            .filter(
                Defect.project_id == project.id,
                Defect.severity.in_([DefectSeverity.CRITICAL, DefectSeverity.HIGH])
            )
            .scalar()
            or 0
        )
        
        # Risk calculation
        defect_ratio = (open_defects / max(1, tc_count)) * 50
        coverage_ratio = (req_count / max(1, tc_count)) * 30
        criticality_ratio = (critical_def / max(1, open_defects + 1)) * 20 if open_defects > 0 else 0
        risk_score = min(100, max(0, defect_ratio + coverage_ratio + criticality_ratio))
        
        metrics.append(
            ProjectMetrics(
                project_id=project.id,
                project_name=project.name,
                requirements_count=req_count,
                test_cases_count=tc_count,
                defects_open=open_defects,
                defects_critical=critical_def,
                risk_score=round(risk_score, 1),
                coverage_percent=round((tc_count / max(1, req_count) * 100), 1) if req_count > 0 else 0,
            )
        )
    
    return metrics


@router.get("/activity", response_model=List[ActivityLog])
def get_activity_feed(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent activity across all projects."""
    activities = []
    
    # Get recent defects
    recent_defects = (
        db.query(Defect, Project)
        .join(Project)
        .order_by(Defect.created_at.desc())
        .limit(limit)
        .all()
    )
    
    for defect, project in recent_defects:
        activities.append(
            ActivityLog(
                id=defect.id,
                timestamp=defect.created_at,
                activity_type="defect_created",
                description=f"Defect created: {defect.title}",
                project_name=project.name,
            )
        )
    
    # Get recent releases
    recent_releases = (
        db.query(Release, Project)
        .join(Project)
        .order_by(Release.created_at.desc())
        .limit(limit)
        .all()
    )
    
    for release, project in recent_releases:
        activities.append(
            ActivityLog(
                id=release.id,
                timestamp=release.created_at,
                activity_type="release_created",
                description=f"Release created: {release.version}",
                project_name=project.name,
            )
        )
    
    # Sort by timestamp descending and return top N
    return sorted(activities, key=lambda x: x.timestamp, reverse=True)[:limit]


class TrendPoint(BaseModel):
    date: str
    coverage: float
    defects: int
    risk: float


@router.get("/trends", response_model=List[TrendPoint])
def get_trends(project_id: Optional[int] = None, months: int = 6, db: Session = Depends(get_db)):
    """Return recent quality trend points (coverage, defects, risk) per month.

    If `project_id` is provided, trends are for that project; otherwise aggregated across projects.
    """
    # Fetch metrics; we'll bucket by year-month
    query = db.query(QualityMetric)
    if project_id:
        query = query.filter(QualityMetric.project_id == project_id)

    metrics = query.order_by(QualityMetric.metric_date.desc()).all()

    # Bucket by YYYY-MM -> take the latest metric in that month
    buckets = {}
    for m in metrics:
        key = m.metric_date.strftime("%Y-%m") if m.metric_date else None
        if not key:
            continue
        if key not in buckets:
            buckets[key] = m

    # Sort months ascending and take the last `months` entries
    keys = sorted(buckets.keys())[-months:]
    result = []
    for k in keys:
        m = buckets[k]
        label = m.metric_date.strftime("%b %Y") if m.metric_date else k
        result.append(TrendPoint(
            date=label,
            coverage=round(getattr(m, 'test_coverage_percent', getattr(m, 'coverage_percent', 0.0)) or 0.0, 1),
            defects=int(getattr(m, 'defects_open', 0) or 0),
            risk=round(getattr(m, 'overall_risk_score', getattr(m, 'risk_score', 0.0)) or 0.0, 1),
        ))

    return result
