from datetime import datetime

from pydantic import BaseModel, Field


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=125, examples=["users.read"])
    display_name: str = Field(..., min_length=2, max_length=255, examples=["Read Users"])
    guard_name: str = Field(default="api", max_length=125, examples=["api"])


class PermissionUpdate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=255, examples=["Read Users"])


class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    guard_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}