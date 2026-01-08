"""Database models for VeriShip QA Platform."""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Table, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


# ========== Authentication & Users ==========

class User(Base):
    """User accounts for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    first_name = Column(String(255))
    last_name = Column(String(255))
    role = Column(String(100), default="member")  # admin, lead, member, viewer
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    assigned_projects = relationship("Project", back_populates="assigned_users", secondary="user_project_assignment")


class UserProjectAssignment(Base):
    """Association between users and projects."""
    __tablename__ = "user_project_assignment"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(String(100), default="member")  # lead, member, viewer, etc
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== Enums ==========

class ProjectStatus(str, PyEnum):
    """Project status enumeration."""
    PLANNING = "planning"
    IN_PROGRESS = "in-progress"
    ON_TRACK = "on-track"
    AT_RISK = "at-risk"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class RequirementStatus(str, PyEnum):
    """Requirement status enumeration."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class TestStatus(str, PyEnum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    IN_PROGRESS = "in-progress"


class DefectSeverity(str, PyEnum):
    """Defect severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class DefectStatus(str, PyEnum):
    """Defect status."""
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class ReleaseStatus(str, PyEnum):
    """Release status."""
    PLANNING = "planning"
    IN_TESTING = "in-testing"
    READY = "ready"
    APPROVED = "approved"
    RELEASED = "released"
    ROLLBACK = "rollback"


class ApprovalStatus(str, PyEnum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


# ========== Module 1: Requirements & Planning ==========

class Project(Base):
    """Core project entity."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    start_date = Column(DateTime, default=datetime.utcnow)
    target_release_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    defects = relationship("Defect", back_populates="project", cascade="all, delete-orphan")
    releases = relationship("Release", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="project", cascade="all, delete-orphan")
    assigned_users = relationship("User", back_populates="assigned_projects", secondary="user_project_assignment")


class Requirement(Base):
    """Requirements with AI analysis."""
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    requirement_id = Column(String(100), nullable=False)  # e.g., USER-123
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(JSON, default=list)  # AI-generated or manual
    status = Column(Enum(RequirementStatus), default=RequirementStatus.DRAFT)
    
    # AI Analysis
    clarity_score = Column(Float, default=0.0)  # 0-100
    is_testable = Column(Boolean, default=True)
    missing_criteria = Column(JSON, default=list)  # AI suggestions
    ambiguous_terms = Column(JSON, default=list)  # Flagged issues
    
    priority = Column(Integer, default=1)  # 1=High, 5=Low
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    test_cases = relationship("TestCase", back_populates="requirement")
    
    __table_args__ = (UniqueConstraint('project_id', 'requirement_id', name='uq_proj_req_id'),)


class AcceptanceCriteria(Base):
    """Individual acceptance criteria."""
    __tablename__ = "acceptance_criteria"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    criterion = Column(Text, nullable=False)
    is_met = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== Module 2: Test Design & Coverage ==========

class TestCase(Base):
    """Test cases with traceability."""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=True, index=True)
    test_case_id = Column(String(100), nullable=False)  # e.g., TC-001
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Test Type
    test_type = Column(String(50))  # unit, integration, e2e, manual, performance
    priority = Column(Integer, default=1)  # 1=High, 5=Low
    
    # Risk & Coverage
    risk_area = Column(String(255))  # security, performance, data, compliance
    edge_cases = Column(JSON, default=list)  # AI-suggested edge cases
    coverage_status = Column(Float, default=0.0)  # 0-100%
    # Lifecycle status: ongoing, completed, archived
    status = Column(String(50), default="ongoing")
    
    # Steps (for manual tests)
    test_steps = Column(JSON, default=list)
    expected_result = Column(Text)
    
    automation_script = Column(Text)  # For automated tests
    is_automated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="test_cases")
    requirement = relationship("Requirement", back_populates="test_cases")
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint('project_id', 'test_case_id', name='uq_proj_test_id'),)


class TestSuite(Base):
    """Grouping of test cases for execution."""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_case_ids = Column(JSON, default=list)  # Array of TestCase IDs
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== Module 3: Test Execution & Automation ==========

class TestExecution(Base):
    """Test execution runs and results."""
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    test_run_id = Column(String(100), nullable=False)  # e.g., RUN-001
    
    status = Column(Enum(TestStatus), default=TestStatus.IN_PROGRESS)
    duration_seconds = Column(Integer)
    
    # Execution Details
    executed_by = Column(String(255))  # User or CI system
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Results
    output = Column(Text)  # Logs, error messages
    screenshots = Column(JSON, default=list)  # For UI tests
    error_message = Column(Text)
    
    # Flakiness
    is_flaky = Column(Boolean, default=False)
    flaky_count = Column(Integer, default=0)
    
    # Environment
    environment = Column(String(50))  # dev, staging, prod
    browser = Column(String(50))  # For UI tests
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_case = relationship("TestCase", back_populates="executions")


class CI_CDPipeline(Base):
    """CI/CD integration tracking."""
    __tablename__ = "ci_cd_pipelines"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    pipeline_name = Column(String(255))
    pipeline_url = Column(String(255))
    status = Column(String(50))  # success, failed, running
    triggered_at = Column(DateTime)
    completed_at = Column(DateTime)
    test_results = Column(JSON, default=dict)  # Summary of test results


# ========== Module 4: Defect Management & Risk Scoring ==========

class Defect(Base):
    """Bug/defect tracking with AI analysis."""
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    defect_id = Column(String(100), nullable=False)  # e.g., DEF-001
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Severity & Status
    severity = Column(Enum(DefectSeverity), default=DefectSeverity.MEDIUM)
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN)
    
    # AI Analysis
    root_cause = Column(String(255))
    business_impact = Column(String(50))  # critical, high, medium, low
    release_risk_score = Column(Float, default=0.0)  # 0-100
    
    # Recurrence Prediction
    likely_to_recur = Column(Boolean, default=False)
    recurrence_probability = Column(Float, default=0.0)  # 0-1
    
    # Related Data
    found_by = Column(String(255))
    assigned_to = Column(String(255))
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)
    related_defect_ids = Column(JSON, default=list)  # For duplicates
    
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="defects")


class QualityMetric(Base):
    """Aggregated quality metrics."""
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    metric_date = Column(DateTime, default=datetime.utcnow)
    
    # Metrics
    total_requirements = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    test_coverage_percent = Column(Float, default=0.0)
    
    tests_passed = Column(Integer, default=0)
    tests_failed = Column(Integer, default=0)
    tests_skipped = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    
    defects_open = Column(Integer, default=0)
    defects_critical = Column(Integer, default=0)
    defects_high = Column(Integer, default=0)
    
    overall_risk_score = Column(Float, default=0.0)  # 0-100


# ========== Module 5: Release Readiness & Delivery Gate ==========

class Release(Base):
    """Release versions with governance."""
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    release_id = Column(String(100), nullable=False)  # e.g., v1.2.3
    
    version = Column(String(50))
    status = Column(Enum(ReleaseStatus), default=ReleaseStatus.PLANNING)
    
    # Planning
    planned_release_date = Column(DateTime)
    actual_release_date = Column(DateTime)
    
    # Quality Gate
    requirements_met = Column(Boolean, default=False)
    minimum_test_coverage = Column(Float, default=80.0)
    actual_test_coverage = Column(Float, default=0.0)
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0)  # 0-100
    blockers = Column(JSON, default=list)  # Blocking issues
    critical_defects_fixed = Column(Boolean, default=False)
    
    # Release Decision
    go_no_go_decision = Column(String(50))  # "go", "no-go", "conditional"
    decision_rationale = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="releases")
    approvals = relationship("ReleaseApproval", back_populates="release", cascade="all, delete-orphan")


class ReleaseApproval(Base):
    """Release approval workflow."""
    __tablename__ = "release_approvals"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id"), nullable=False)
    
    approver_name = Column(String(255), nullable=False)
    approver_role = Column(String(100))  # QA, PM, Engineering, Executive
    
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments = Column(Text)
    
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    release = relationship("Release", back_populates="approvals")


# ========== Module 6: Post-Release QA Intelligence ==========

class ProductionIssue(Base):
    """Production issues and incidents."""
    __tablename__ = "production_issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    release_id = Column(Integer, ForeignKey("releases.id"), nullable=True)
    
    issue_id = Column(String(100), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    
    # Classification
    category = Column(String(100))  # crash, hang, data_loss, performance, security
    severity = Column(Enum(DefectSeverity))
    
    # Root Cause
    related_defect_id = Column(Integer, ForeignKey("defects.id"), nullable=True)
    root_cause_analysis = Column(Text)
    
    # Impact
    affected_users = Column(Integer, default=0)
    detected_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Learning
    why_escaped_qa = Column(Text)  # AI analysis
    preventive_actions = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class QAInsight(Base):
    """AI-generated QA insights and predictions."""
    __tablename__ = "qa_insights"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    insight_type = Column(String(100))  # prediction, recommendation, risk_alert
    title = Column(String(255))
    description = Column(Text)
    
    confidence_score = Column(Float)  # 0-1
    action_items = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== Team & Organization ==========

class TeamMember(Base):
    """Team member assignments."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(100))  # QA, Dev, PM, Lead
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="team_members")
