"""
Pydantic models for guest user management.
"""
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class GuestUser(BaseModel):
    """Guest user record — auto-created on first visit, stored in MongoDB."""
    user_id: str = Field(default_factory=lambda: f"guest_{uuid.uuid4().hex[:12]}")
    display_name: str = "Guest"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RegisterGuestRequest(BaseModel):
    """Register a new guest or sync an existing one."""
    user_id: str = Field("", description="Existing guest ID from localStorage, empty for new")
    display_name: str = "Guest"


class RegisterGuestResponse(BaseModel):
    """Response after guest registration."""
    user_id: str
    display_name: str
    is_new: bool = True
