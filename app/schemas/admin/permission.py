from pydantic import BaseModel, Field


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=125, examples=["users.read"])
    description: str | None = Field(None, max_length=255, examples=["Read Users"])
    guard_name: str = Field(default="api", max_length=125, examples=["api"])


class PermissionUpdate(BaseModel):
    description: str | None = Field(None, max_length=255, examples=["Read Users"])
