from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.permission import PermissionResponse


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=125, examples=["editor"])
    display_name: str = Field(..., min_length=2, max_length=255, examples=["Editor"])
    guard_name: str = Field(default="api", max_length=125, examples=["api"])


class RoleUpdate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=255, examples=["Editor"])


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    guard_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleDetailResponse(RoleResponse):
    """Role response that includes its assigned permissions."""
    permissions: list[PermissionResponse] = []


# ── assignment request bodies ─────────────────────────────────────────────────

class AssignPermissionRequest(BaseModel):
    permission_id: int = Field(..., gt=0, examples=[1])


class AssignPermissionsRequest(BaseModel):
    """Sync (replace) the entire permission set for a role."""
    permission_ids: list[int] = Field(..., min_length=0, examples=[[1, 2, 3]])