"""Audit logging utilities for tracking data modifications."""

from functools import wraps
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import AuditLog


def log_audit(
    db: Session,
    user_id: Optional[int],
    table_name: str,
    record_id: int,
    operation: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Create an audit log entry for a data operation.
    
    Args:
        db: Database session
        user_id: ID of user performing the operation
        table_name: Name of table being modified
        record_id: ID of record being modified
        operation: "INSERT", "UPDATE", or "DELETE"
        old_values: Previous values (for UPDATE/DELETE)
        new_values: New values (for INSERT/UPDATE)
    
    Returns:
        True if audit log was successfully created, False otherwise
    """
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.utcnow()
        )
        db.add(audit_entry)
        db.flush()  # Flush but don't commit - let caller handle transactions
        return True
    except Exception as e:
        print(f"WARNING: Failed to create audit log: {e}")
        return False


def audit_create(table_name: str) -> Callable:
    """
    Decorator to automatically log INSERT operations.
    
    Usage:
        @audit_create('users')
        def create_user(user_data, db, current_user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Extract db and current_user from kwargs
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if db and current_user and result and hasattr(result, 'id'):
                # Convert result to dict for logging
                result_dict = {}
                if hasattr(result, '__table__'):
                    for column in result.__table__.columns:
                        result_dict[column.name] = getattr(result, column.name, None)
                
                log_audit(
                    db=db,
                    user_id=current_user.id,
                    table_name=table_name,
                    record_id=result.id,
                    operation="INSERT",
                    new_values=result_dict
                )
            return result
        return wrapper
    return decorator


def audit_update(table_name: str) -> Callable:
    """
    Decorator to automatically log UPDATE operations.
    
    Usage:
        @audit_update('users')
        def update_user(user_id, updates, db, current_user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract record before modification
            db = kwargs.get('db')
            record_id = None
            old_values = None
            
            # This is tricky - would need to know which arg is the ID
            # Better approach: log after the update
            result = func(*args, **kwargs)
            
            if db and result and hasattr(result, 'id'):
                current_user = kwargs.get('current_user')
                # Convert result to dict for logging
                result_dict = {}
                if hasattr(result, '__table__'):
                    for column in result.__table__.columns:
                        result_dict[column.name] = getattr(result, column.name, None)
                
                log_audit(
                    db=db,
                    user_id=current_user.id if current_user else None,
                    table_name=table_name,
                    record_id=result.id,
                    operation="UPDATE",
                    new_values=result_dict
                )
            return result
        return wrapper
    return decorator


def audit_delete(table_name: str) -> Callable:
    """
    Decorator to automatically log DELETE operations.
    
    Usage:
        @audit_delete('users')
        def delete_user(user_id, db, current_user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if db and result:
                # Extract record_id from result if possible
                record_id = result.get('id') if isinstance(result, dict) else None
                if record_id:
                    log_audit(
                        db=db,
                        user_id=current_user.id if current_user else None,
                        table_name=table_name,
                        record_id=record_id,
                        operation="DELETE"
                    )
            return result
        return wrapper
    return decorator
