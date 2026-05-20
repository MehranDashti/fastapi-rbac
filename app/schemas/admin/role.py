from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=125, examples=["editor"])
    description: str | None = Field(None, max_length=255, examples=["Editor"])
    guard_name: str = Field(default="api", max_length=125, examples=["api"])


class RoleUpdate(BaseModel):
    description: str | None = Field(None, max_length=255, examples=["Editor"])


class AssignPermissionRequest(BaseModel):
    permission_id: int = Field(..., gt=0, examples=[1])


class AssignPermissionsRequest(BaseModel):
    """Sync (replace) the entire permission set for a role."""
    permission_ids: list[int] = Field(..., min_length=0, examples=[[1, 2, 3]])
