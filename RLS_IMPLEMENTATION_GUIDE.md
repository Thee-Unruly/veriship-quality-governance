# VeriShip RLS & Authorization Implementation Guide

## Overview

This document describes the complete Row-Level Security (RLS) and authorization system implemented for the VeriShip QA platform. The implementation combines **database-level RLS policies** with **application-level permission checks** for comprehensive access control.

---

## Architecture

### Two-Layer Authorization Model

```
┌─────────────────────────────┐
│  Application Layer          │
│  - FastAPI Endpoints        │
│  - Role-Based Permissions   │
│  - Audit Logging            │
└──────────────┬──────────────┘
               │
     ┌─────────▼──────────┐
     │ Database Layer     │
     │ - RLS Policies     │
     │ - Row Filtering    │
     └────────────────────┘
```

**Why Two Layers?**
- **Application layer**: Fast, flexible, user-friendly error messages
- **Database layer**: Protection against direct DB access, compliance requirement

---

## Components

### 1. Database Models

#### New: `AuditLog` Model
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: int (PK)
    user_id: int (FK to users)
    table_name: str  # e.g., "requirements", "defects"
    record_id: int   # ID of affected record
    operation: str   # "INSERT", "UPDATE", "DELETE"
    old_values: JSON # Previous state (for UPDATE/DELETE)
    new_values: JSON # New state (for INSERT/UPDATE)
    created_at: datetime (indexed)
```

#### Enhanced: `UserProjectAssignment` Model
```python
role: str  # "admin", "lead", "member", "tester", "viewer"
```

### 2. Role Hierarchy

| Role    | Hierarchy | Permissions      | Use Case                    |
|---------|-----------|-------------------|---------------------------|
| admin   | 5         | read, create, update, delete | System administrators     |
| lead    | 4         | read, create, update, delete | Project managers/QA leads |
| member  | 3         | read, create, update | Test engineers             |
| tester  | 2         | read, create | Test executors             |
| viewer  | 1         | read | Stakeholders               |

### 3. Authorization Helpers (`dependencies.py`)

#### Core Functions

```python
# Access verification
assert_project_access(db, project_id, user_id)
# Raises 403 if user not assigned to project

# Permission-based checks
assert_read_permission(db, project_id, user_id)
assert_create_permission(db, project_id, user_id)
assert_update_permission(db, project_id, user_id)
assert_delete_permission(db, project_id, user_id)
# Raises 403 if role doesn't have permission

# User utilities
get_user_project_ids(db, user_id) -> List[int]
get_user_role_in_project(db, project_id, user_id) -> str
```

#### Audit Logging

```python
audit_log(
    db: Session,
    user_id: int,
    table_name: str,
    record_id: int,
    operation: str,  # "INSERT", "UPDATE", "DELETE"
    old_values: Dict = None,
    new_values: Dict = None
)
```

### 4. PostgreSQL RLS Policies

Implemented in migration: `001_enable_rls_policies.py`

**Protected Tables:**
- `projects` - User can only access projects they're assigned to
- `requirements` - Scoped to project access
- `test_cases` - Scoped to project access
- `defects` - Scoped to project access
- `releases` - Scoped to project access

**Policy Example for `requirements`:**
```sql
CREATE POLICY requirements_select_policy ON requirements
FOR SELECT
USING (
    project_id IN (
        SELECT project_id FROM user_project_assignment 
        WHERE user_id = current_user_id()
    )
);
```

---

## Usage Guide

### 1. Protecting an Endpoint

**Example: Create a test case**

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.models import User, TestCase, Project
from app.dependencies import assert_create_permission, audit_log

@router.post("/test-cases")
def create_test_case(
    data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization: Check if user can create in this project
    assert_create_permission(db, data.project_id, current_user.id)
    
    # Create the test case
    test_case = TestCase(**data.dict())
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    
    # Audit log
    audit_log(
        db=db,
        user_id=current_user.id,
        table_name="test_cases",
        record_id=test_case.id,
        operation="INSERT",
        new_values=test_case.__dict__
    )
    
    return test_case
```

### 2. Querying User-Scoped Data

**Example: Get all projects for current user**

```python
from app.dependencies import get_user_project_ids

@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all projects the user has access to
    project_ids = get_user_project_ids(db, current_user.id)
    
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    return projects
```

### 3. Role-Based Operations

**Example: Only allow leads to create projects**

```python
@router.post("/projects")
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin (global role)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create projects")
    
    project = Project(**data.dict())
    db.add(project)
    db.commit()
    return project
```

### 4. Audit Trail Queries

```python
@router.get("/audit/defects/{defect_id}")
def get_defect_history(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all changes to this defect
    history = db.query(AuditLog).filter(
        AuditLog.table_name == "defects",
        AuditLog.record_id == defect_id
    ).order_by(AuditLog.created_at.desc()).all()
    
    return history
```

---

## Migration Steps

### Step 1: Apply RLS Migration

```bash
# Assuming you have Alembic configured
cd backend
alembic upgrade head
```

This creates:
- `audit_logs` table with proper indexes
- RLS policies on `projects`, `requirements`, `test_cases`, `defects`, `releases`

### Step 2: Update Application Code

The authorization helpers are automatically available through:
```python
from app.dependencies import (
    assert_project_access,
    assert_create_permission,
    assert_read_permission,
    assert_update_permission,
    assert_delete_permission,
    audit_log,
    get_user_project_ids,
    get_user_role_in_project
)
from app.auth import get_current_user
```

### Step 3: Update All Endpoints

For each endpoint that manipulates data:

```python
# 1. Add current_user dependency
current_user: User = Depends(get_current_user)

# 2. Add authorization check
assert_create_permission(db, project_id, current_user.id)

# 3. Add audit logging (optional but recommended)
audit_log(db, current_user.id, table_name, record_id, "INSERT", new_values=data)
```

---

## Security Best Practices

### ✅ Do

1. **Always authenticate endpoints** - Add `get_current_user` dependency
2. **Check permissions early** - Validate access before querying
3. **Log sensitive operations** - Track creates/updates/deletes
4. **Scope queries by project** - Filter by `user_project_ids`
5. **Use parameterized queries** - SQLAlchemy handles this automatically

### ❌ Don't

1. **Skip RLS checks** - Both app and DB checks are needed
2. **Assume JWT is enough** - Token validity ≠ resource access
3. **Allow cross-project access** - Always verify project assignment
4. **Expose audit logs directly** - Filter by user's accessible projects first
5. **Hardcode permissions** - Use the permission system

---

## Testing RLS

### Unit Test Example

```python
import pytest
from app.models import User, Project, UserProjectAssignment, Requirement
from app.dependencies import assert_project_access

def test_user_cannot_access_unassigned_project(db_session):
    """User should not access projects they're not assigned to."""
    
    # Create users and projects
    user1 = User(username="user1", email="user1@test.com", role="member")
    user2 = User(username="user2", email="user2@test.com", role="member")
    project = Project(name="Project A")
    
    db_session.add_all([user1, user2, project])
    db_session.flush()
    
    # Only assign user1 to project
    assignment = UserProjectAssignment(user_id=user1.id, project_id=project.id, role="member")
    db_session.add(assignment)
    db_session.commit()
    
    # user1 should have access
    assert_project_access(db_session, project.id, user1.id)  # Should not raise
    
    # user2 should not have access
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        assert_project_access(db_session, project.id, user2.id)
    assert exc.value.status_code == 403
```

---

## Monitoring & Auditing

### View Recent Changes

```sql
-- Get last 10 operations
SELECT * FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 10;

-- Changes to a specific record
SELECT * FROM audit_logs 
WHERE table_name = 'defects' AND record_id = 42
ORDER BY created_at;

-- Changes by a user
SELECT * FROM audit_logs 
WHERE user_id = 5 
ORDER BY created_at DESC;

-- Deletions audit
SELECT * FROM audit_logs 
WHERE operation = 'DELETE' 
ORDER BY created_at DESC;
```

---

## Compliance & Regulations

This RLS implementation helps with:

- **SOC 2** - Row-level access controls, audit trails
- **GDPR** - Data access restrictions, audit logging
- **ISO 27001** - Access control policies, audit logs
- **HIPAA** - Scoped data access (if used in healthcare)

---

## Troubleshooting

### Issue: "Not authorized to access this project"

**Cause**: User is not assigned to the project in `user_project_assignment`

**Solution**: 
```python
# Add user to project
assignment = UserProjectAssignment(
    user_id=user_id,
    project_id=project_id,
    role="member"
)
db.add(assignment)
db.commit()
```

### Issue: Audit logs growing too large

**Solution**: Archive old logs
```python
# Archive logs older than 90 days
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=90)
old_logs = db.query(AuditLog).filter(AuditLog.created_at < cutoff).all()
# Save to archive table/file, then delete
```

---

## Next Steps

1. **Implement decorators** - Use `@audit_update`, `@audit_delete` for cleaner code
2. **Add event notifications** - Alert admins of suspicious activity
3. **Role customization** - Allow orgs to define custom roles
4. **Data masking** - Mask sensitive fields in audit logs
5. **Compliance reporting** - Generate audit reports for compliance

---

## References

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [OWASP Authorization Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
