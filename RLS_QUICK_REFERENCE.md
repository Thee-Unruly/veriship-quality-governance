# Quick Authorization Implementation Template

## Copy-Paste Template for Adding Authorization to Routes

### Template 1: READ Endpoints (View-only access)

```python
from fastapi import Depends, HTTPException
from app.auth import get_current_user
from app.dependencies import assert_read_permission
from app.models import User, YourModel

@router.get("/{item_id}")
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADD THIS
):
    """Get a specific item."""
    item = db.query(YourModel).filter(YourModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # ADD THESE LINES:
    assert_read_permission(db, item.project_id, current_user.id)
    
    return item
```

### Template 2: CREATE Endpoints (Must create in authorized project)

```python
from fastapi import Depends
from app.auth import get_current_user
from app.dependencies import assert_create_permission, audit_log
from app.models import User

@router.post("/")
def create_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADD THIS
):
    """Create a new item."""
    
    # ADD THIS LINE:
    assert_create_permission(db, data.project_id, current_user.id)
    
    item = YourModel(**data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # ADD THIS BLOCK (optional but recommended):
    audit_log(
        db=db,
        user_id=current_user.id,
        table_name="your_table_name",
        record_id=item.id,
        operation="INSERT",
        new_values={
            "field1": item.field1,
            "field2": item.field2,
            # ... include key fields
        }
    )
    
    return item
```

### Template 3: UPDATE Endpoints (Requires update permission)

```python
from app.dependencies import assert_update_permission, audit_log

@router.put("/{item_id}")
def update_item(
    item_id: int,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADD THIS
):
    """Update an existing item."""
    item = db.query(YourModel).filter(YourModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # ADD THIS LINE:
    assert_update_permission(db, item.project_id, current_user.id)
    
    # Store old values for audit
    old_values = {col.name: getattr(item, col.name) for col in item.__table__.columns}
    
    # Update fields
    for key, value in data.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    # ADD THIS BLOCK (optional but recommended):
    new_values = {col.name: getattr(item, col.name) for col in item.__table__.columns}
    audit_log(
        db=db,
        user_id=current_user.id,
        table_name="your_table_name",
        record_id=item.id,
        operation="UPDATE",
        old_values=old_values,
        new_values=new_values
    )
    
    return item
```

### Template 4: DELETE Endpoints (Requires delete permission)

```python
from app.dependencies import assert_delete_permission, audit_log

@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADD THIS
):
    """Delete an item."""
    item = db.query(YourModel).filter(YourModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # ADD THIS LINE:
    assert_delete_permission(db, item.project_id, current_user.id)
    
    # ADD THIS BLOCK (optional but recommended):
    old_values = {col.name: getattr(item, col.name) for col in item.__table__.columns}
    audit_log(
        db=db,
        user_id=current_user.id,
        table_name="your_table_name",
        record_id=item.id,
        operation="DELETE",
        old_values=old_values
    )
    
    db.delete(item)
    db.commit()
    
    return {"status": "deleted"}
```

### Template 5: LIST Endpoints (Filtered by user's projects)

```python
from app.dependencies import get_user_project_ids

@router.get("/")
def list_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADD THIS
):
    """List all items the user has access to."""
    
    # ADD THESE LINES:
    user_project_ids = get_user_project_ids(db, current_user.id)
    
    if not user_project_ids:
        return []
    
    items = db.query(YourModel).filter(
        YourModel.project_id.in_(user_project_ids)
    ).all()
    
    return items
```

---

## Complete Example: Defects Routes

### Before (Unprotected)
```python
@router.post("/{project_id}/defects")
def create_defect(project_id: int, defect: DefectCreate, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_defect = Defect(**defect.dict(), project_id=project_id)
    db.add(new_defect)
    db.commit()
    return new_defect
```

### After (Protected)
```python
from app.auth import get_current_user
from app.dependencies import assert_create_permission, audit_log

@router.post("/{project_id}/defects")
def create_defect(
    project_id: int,
    defect: DefectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← ADDED
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # ← ADDED: Permission check
    assert_create_permission(db, project_id, current_user.id)
    
    new_defect = Defect(**defect.dict(), project_id=project_id)
    db.add(new_defect)
    db.commit()
    db.refresh(new_defect)
    
    # ← ADDED: Audit logging
    audit_log(
        db=db,
        user_id=current_user.id,
        table_name="defects",
        record_id=new_defect.id,
        operation="INSERT",
        new_values={
            "title": new_defect.title,
            "severity": new_defect.severity,
            "project_id": new_defect.project_id
        }
    )
    
    return new_defect
```

---

## Required Imports (Copy to Top of File)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User  # ← ADDED
from app.auth import get_current_user  # ← ADDED
from app.dependencies import (  # ← ADDED
    assert_read_permission,
    assert_create_permission,
    assert_update_permission,
    assert_delete_permission,
    assert_project_access,
    get_user_project_ids,
    audit_log
)
```

---

## Common Patterns

### Pattern 1: User can only see/modify their own submissions

```python
# In create endpoint
assert_create_permission(db, project_id, current_user.id)

# In update - verify same user or admin
if item.created_by_id != current_user.id and current_user.role != "admin":
    raise HTTPException(status_code=403, detail="Can only edit your own items")
```

### Pattern 2: Lead can modify all project items

```python
# Check user's role in project
role = get_user_role_in_project(db, project_id, current_user.id)
if role not in ["admin", "lead"]:
    raise HTTPException(status_code=403, detail="Only leads can modify")
```

### Pattern 3: Viewer role prevents writes

```python
# Read-only check
role = get_user_role_in_project(db, project_id, current_user.id)
if role == "viewer":
    raise HTTPException(status_code=403, detail="Viewers cannot modify items")
```

---

## Testing Template

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_cannot_create_in_unassigned_project(authorized_token, db_session):
    """User with token for project A cannot create in project B."""
    
    # Try to create in unauthorized project
    response = client.post(
        "/api/defects",
        json={"title": "Bug", "project_id": 999},  # Unauthorized project
        headers={"Authorization": f"Bearer {authorized_token}"}
    )
    
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()

def test_user_can_create_in_assigned_project(authorized_token):
    """User can create in their assigned project."""
    
    response = client.post(
        "/api/defects",
        json={"title": "Bug", "project_id": 1},  # Authorized project
        headers={"Authorization": f"Bearer {authorized_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Bug"
```

---

## Checklist for Each Route File

- [ ] Added imports: `User`, `get_current_user`, permission functions
- [ ] All CREATE endpoints: Added `assert_create_permission()`
- [ ] All UPDATE endpoints: Added `assert_update_permission()`
- [ ] All DELETE endpoints: Added `assert_delete_permission()`
- [ ] All READ endpoints: Added `assert_read_permission()` or `assert_project_access()`
- [ ] All LIST endpoints: Use `get_user_project_ids()` to filter results
- [ ] Optional: Added audit logging to CREATE/UPDATE/DELETE
- [ ] Tested with unauthorized user token
- [ ] Tested with authorized user token

---

## Quick Reference: Function Signatures

```python
# Check access (minimal)
assert_project_access(db: Session, project_id: int, user_id: int)
# → Raises 403 if not assigned

# Check permission (recommended)
assert_read_permission(db: Session, project_id: int, user_id: int)
assert_create_permission(db: Session, project_id: int, user_id: int)
assert_update_permission(db: Session, project_id: int, user_id: int)
assert_delete_permission(db: Session, project_id: int, user_id: int)
# → Raises 403 if role lacks permission

# Get user data
get_user_project_ids(db: Session, user_id: int) -> list[int]
get_user_role_in_project(db: Session, project_id: int, user_id: int) -> str

# Audit
audit_log(db, user_id, table_name, record_id, operation, old_values, new_values)
```

---

## Need Help?

See **RLS_IMPLEMENTATION_GUIDE.md** for detailed documentation and examples.
