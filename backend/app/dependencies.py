# app/dependencies.py
"""Authorization and access control helpers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import UserProjectAssignment, User
from datetime import datetime
from typing import Optional, Dict, Any

# ===== Role Definitions =====
ROLE_HIERARCHY = {
    "admin": 5,        # Full system access
    "lead": 4,         # Project lead, can create/modify
    "member": 3,       # Can create/modify own work
    "tester": 2,       # Can only execute tests, view data
    "viewer": 1,       # Read-only access
}

# Permission matrix: role -> operations allowed
ROLE_PERMISSIONS = {
    "admin": ["read", "create", "update", "delete"],
    "lead": ["read", "create", "update", "delete"],
    "member": ["read", "create", "update"],
    "tester": ["read", "create"],
    "viewer": ["read"],
}


def assert_project_access(db: Session, project_id: int, user_id: int) -> UserProjectAssignment:
    """
    Verify user has access to a project.
    Raises 403 if not authorized.
    Returns the assignment if authorized.
    """
    assignment = db.query(UserProjectAssignment).filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return assignment


def assert_permission(
    db: Session, 
    project_id: int, 
    user_id: int, 
    operation: str
) -> UserProjectAssignment:
    """
    Verify user has permission for an operation on a project.
    
    Args:
        db: Database session
        project_id: Project ID to check access
        user_id: User ID attempting operation
        operation: "read", "create", "update", "delete"
    
    Returns:
        UserProjectAssignment if authorized
    
    Raises:
        HTTPException 403 if not authorized
    """
    assignment = assert_project_access(db, project_id, user_id)
    
    role = assignment.role or "viewer"
    allowed_ops = ROLE_PERMISSIONS.get(role, ["read"])
    
    if operation not in allowed_ops:
        raise HTTPException(
            status_code=403, 
            detail=f"Role '{role}' does not have '{operation}' permission"
        )
    
    return assignment


def assert_read_permission(db: Session, project_id: int, user_id: int):
    """Check read access."""
    return assert_permission(db, project_id, user_id, "read")


def assert_create_permission(db: Session, project_id: int, user_id: int):
    """Check create access."""
    return assert_permission(db, project_id, user_id, "create")


def assert_update_permission(db: Session, project_id: int, user_id: int):
    """Check update access."""
    return assert_permission(db, project_id, user_id, "update")


def assert_delete_permission(db: Session, project_id: int, user_id: int):
    """Check delete access."""
    return assert_permission(db, project_id, user_id, "delete")


def get_user_project_ids(db: Session, user_id: int) -> list[int]:
    """Get all project IDs a user has access to."""
    return [
        a.project_id for a in db.query(UserProjectAssignment)
        .filter(UserProjectAssignment.user_id == user_id).all()
    ]


def get_user_role_in_project(db: Session, project_id: int, user_id: int) -> Optional[str]:
    """Get a user's role in a specific project."""
    assignment = db.query(UserProjectAssignment).filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    return assignment.role if assignment else None


def audit_log(
    db: Session,
    user_id: int,
    table_name: str,
    record_id: int,
    operation: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
):
    """
    Log an operation for audit trail.
    
    Args:
        db: Database session
        user_id: User performing the operation
        table_name: Name of table being modified
        record_id: ID of record being modified
        operation: "INSERT", "UPDATE", or "DELETE"
        old_values: Previous values (for UPDATE/DELETE)
        new_values: New values (for INSERT/UPDATE)
    """
    try:
        # Import here to avoid circular imports
        from app.models import AuditLog
        
        log = AuditLog(
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.flush()  # Flush but don't commit - let caller handle transaction
    except Exception as e:
        # Log audit failures but don't fail the operation
        print(f"WARNING: Audit logging failed: {e}")