"""Settings routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Setting
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class GeneralSettingsSchema(BaseModel):
    """General settings schema."""
    organization_name: str
    timezone: str
    notification_email: Optional[str] = None


@router.get("/general")
def get_general_settings(db: Session = Depends(get_db)):
    """Get general settings."""
    settings = {}
    
    # Fetch settings from database
    org_name = db.query(Setting).filter(Setting.key == "organization_name").first()
    timezone = db.query(Setting).filter(Setting.key == "timezone").first()
    notification_email = db.query(Setting).filter(Setting.key == "notification_email").first()
    
    settings["organization_name"] = org_name.value if org_name else "VeriShip QA"
    settings["timezone"] = timezone.value if timezone else "UTC"
    settings["notification_email"] = notification_email.value if notification_email else ""
    
    return settings


@router.put("/general")
def update_general_settings(settings: GeneralSettingsSchema, db: Session = Depends(get_db)):
    """Update general settings."""
    # Update or create organization name
    org_name = db.query(Setting).filter(Setting.key == "organization_name").first()
    if org_name:
        org_name.value = settings.organization_name
    else:
        org_name = Setting(key="organization_name", value=settings.organization_name)
        db.add(org_name)
    
    # Update or create timezone
    timezone = db.query(Setting).filter(Setting.key == "timezone").first()
    if timezone:
        timezone.value = settings.timezone
    else:
        timezone = Setting(key="timezone", value=settings.timezone)
        db.add(timezone)
    
    # Update or create notification email
    if settings.notification_email:
        notification_email = db.query(Setting).filter(Setting.key == "notification_email").first()
        if notification_email:
            notification_email.value = settings.notification_email
        else:
            notification_email = Setting(key="notification_email", value=settings.notification_email)
            db.add(notification_email)
    
    db.commit()
    
    return {"status": "success", "message": "Settings updated successfully"}
