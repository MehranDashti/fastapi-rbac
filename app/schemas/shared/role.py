from datetime import datetime

from pydantic import BaseModel

from app.schemas.shared.permission import PermissionResponse


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    guard_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleDetailResponse(RoleResponse):
    """Role response that includes its assigned permissions."""
    permissions: list[PermissionResponse] = []
