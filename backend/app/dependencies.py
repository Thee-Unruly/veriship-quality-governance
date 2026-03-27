# app/dependencies.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import UserProjectAssignment

def assert_project_access(db: Session, project_id: int, user_id: int):
    if not db.query(UserProjectAssignment).filter_by(
        project_id=project_id, user_id=user_id
    ).first():
        raise HTTPException(status_code=403, detail="Not authorized")


def get_user_project_ids(db: Session, user_id: int) -> list[int]:
    return [
        a.project_id for a in db.query(UserProjectAssignment)
        .filter(UserProjectAssignment.user_id == user_id).all()
    ]