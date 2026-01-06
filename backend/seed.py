"""Database seed script for demo data."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    Project, Requirement, TestCase, Defect, Release, ReleaseApproval,
    ProjectStatus, RequirementStatus, DefectSeverity, DefectStatus,
    ReleaseStatus, ApprovalStatus, TeamMember, QualityMetric, User
)
from app.routes.auth import hash_password


def seed_database():
    """Populate database with demo data."""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Project).count() > 0:
        print("Database already seeded. Skipping...")
        return
    
    print("🌱 Seeding database with demo data...")
    
    # === Users ===
    demo_user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=hash_password("testpass"),
        first_name="Test",
        last_name="User",
        role="member",
        is_active=True
    )
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpass"),
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True
    )
    db.add(demo_user)
    db.add(admin_user)
    db.commit()
    
    # === Projects ===
    projects = [
        Project(
            name="Project Alpha",
            description="Core banking platform modernization with regulatory compliance requirements",
            status=ProjectStatus.ON_TRACK,
            target_release_date=datetime.utcnow() + timedelta(days=9),
        ),
        Project(
            name="Project Beta",
            description="Customer-facing mobile application with real-time transaction processing",
            status=ProjectStatus.AT_RISK,
            target_release_date=datetime.utcnow() + timedelta(days=53),
        ),
        Project(
            name="Project Gamma",
            description="Internal risk management dashboard and reporting suite",
            status=ProjectStatus.ON_TRACK,
            target_release_date=datetime.utcnow() + timedelta(days=2),
        ),
    ]
    db.add_all(projects)
    db.commit()
    
    print(f"✅ Created {len(projects)} projects")
    
    # === Team Members ===
    for project in projects:
        team = [
            TeamMember(project_id=project.id, name="Sarah Chen", email="sarah@company.com", role="QA Lead"),
            TeamMember(project_id=project.id, name="Michael Torres", email="michael@company.com", role="QA Engineer"),
            TeamMember(project_id=project.id, name="Jennifer Liu", email="jennifer@company.com", role="Engineering Lead"),
        ]
        db.add_all(team)
    db.commit()
    
    print("✅ Created team members")
    
    # === Requirements ===
    req_count = 0
    for project in projects:
        for i in range(5):
            req = Requirement(
                project_id=project.id,
                requirement_id=f"{project.name.upper()}-REQ-{i+1:03d}",
                title=f"Requirement {i+1}: Core Feature",
                description=f"This is a critical business requirement for {project.name}",
                acceptance_criteria=[
                    "System shall process requests within 2 seconds",
                    "System shall handle 1000 concurrent users",
                    "System shall maintain data consistency",
                ],
                status=RequirementStatus.APPROVED,
                clarity_score=85.0,
                is_testable=True,
                priority=i % 5 + 1,
            )
            db.add(req)
            req_count += 1
    db.commit()
    
    print(f"✅ Created {req_count} requirements")
    
    # === Test Cases ===
    test_count = 0
    for project in projects:
        requirements = db.query(Requirement).filter(Requirement.project_id == project.id).all()
        for i, req in enumerate(requirements):
            for j in range(3):
                tc = TestCase(
                    project_id=project.id,
                    requirement_id=req.id,
                    test_case_id=f"{project.name.upper()}-TC-{i*3+j+1:03d}",
                    title=f"Test Case: {req.title} - Scenario {j+1}",
                    description=f"Automated test for requirement verification",
                    test_type="automated" if j % 2 == 0 else "manual",
                    priority=j % 3 + 1,
                    risk_area="data-integrity" if j == 0 else "performance",
                    coverage_status=85.0 + (j * 5),
                    is_automated=j % 2 == 0,
                )
                db.add(tc)
                test_count += 1
    db.commit()
    
    print(f"✅ Created {test_count} test cases")
    
    # === Defects ===
    defect_count = 0
    for project in projects:
        severities = [DefectSeverity.CRITICAL, DefectSeverity.HIGH, DefectSeverity.MEDIUM]
        for i in range(len(project.requirements) * 2):
            defect = Defect(
                project_id=project.id,
                defect_id=f"{project.name.upper()}-BUG-{i+1:03d}",
                title=f"Defect {i+1}: Critical Issue",
                description="This defect affects core functionality",
                severity=severities[i % 3],
                status=DefectStatus.OPEN if i % 3 == 0 else DefectStatus.IN_PROGRESS,
                business_impact="high" if i % 2 == 0 else "medium",
                release_risk_score=75.0 + (i % 5) * 5,
                found_by="Automated Test" if i % 2 == 0 else "Manual Testing",
                likely_to_recur=i % 3 == 0,
                recurrence_probability=0.3 + (i % 3) * 0.2,
            )
            db.add(defect)
            defect_count += 1
    db.commit()
    
    print(f"✅ Created {defect_count} defects")
    
    # === Quality Metrics ===
    for project in projects:
        metric = QualityMetric(
            project_id=project.id,
            metric_date=datetime.utcnow(),
            total_requirements=5,
            total_test_cases=15,
            test_coverage_percent=85.0,
            tests_passed=12,
            tests_failed=2,
            tests_skipped=1,
            pass_rate=85.7,
            defects_open=8,
            defects_critical=2,
            defects_high=3,
            overall_risk_score=45.0 if project.status == ProjectStatus.ON_TRACK else 72.0,
        )
        db.add(metric)
    db.commit()
    
    print("✅ Created quality metrics")
    
    # === Releases ===
    for project in projects:
        release = Release(
            project_id=project.id,
            release_id=f"{project.name.upper()}-v1.0.0",
            version="1.0.0",
            status=ReleaseStatus.IN_TESTING,
            planned_release_date=project.target_release_date,
            actual_test_coverage=85.0,
            risk_score=45.0 if project.status == ProjectStatus.ON_TRACK else 72.0,
        )
        db.add(release)
        db.commit()
        
        # === Release Approvals ===
        approvers = [
            ReleaseApproval(
                release_id=release.id,
                approver_name="Sarah Chen",
                approver_role="QA Lead",
                status=ApprovalStatus.APPROVED,
                approved_at=datetime.utcnow(),
            ),
            ReleaseApproval(
                release_id=release.id,
                approver_name="Michael Torres",
                approver_role="Product Manager",
                status=ApprovalStatus.PENDING,
            ),
            ReleaseApproval(
                release_id=release.id,
                approver_name="Jennifer Liu",
                approver_role="Engineering Lead",
                status=ApprovalStatus.PENDING,
            ),
        ]
        db.add_all(approvers)
    db.commit()
    
    print("✅ Created releases and approvals")
    
    db.close()
    print("\n✨ Database seeding complete!")


if __name__ == "__main__":
    seed_database()
