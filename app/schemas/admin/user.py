import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role_ids: list[int] = Field(default=[], examples=[[1, 2]])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, digits, and underscores.")
        return v.lower()


class AssignRoleRequest(BaseModel):
    role_id: int = Field(..., gt=0, examples=[1])


class AssignRolesRequest(BaseModel):
    """Sync (replace) the entire role set for a user."""
    role_ids: list[int] = Field(..., min_length=0, examples=[[1, 2]])


class AssignDirectPermissionRequest(BaseModel):
    permission_id: int = Field(..., gt=0, examples=[1])


class AssignDirectPermissionsRequest(BaseModel):
    """Sync (replace) the entire direct-permission set for a user."""
    permission_ids: list[int] = Field(..., min_length=0, examples=[[3, 4]])
