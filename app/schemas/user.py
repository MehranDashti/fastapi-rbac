import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleDetailResponse, RoleResponse


# ── auth request schemas ──────────────────────────────────────────────────────

class UserSignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, examples=["john_doe"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["John Doe"])
    password: str = Field(..., min_length=8, max_length=128, examples=["Secret123"])

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


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


# ── admin user create ─────────────────────────────────────────────────────────

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


# ── role / permission assignment request bodies ───────────────────────────────

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


# ── response schemas ──────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """
    Standard user response — includes roles (with their permissions).
    Used for list endpoints and most single-user responses.
    """
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    roles: list[RoleDetailResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """
    Extended user response — adds a flat list of every permission the user
    holds (via roles + direct grants), computed at serialization time.
    Used for profile and single-user admin endpoints.
    """
    direct_permissions: list[PermissionResponse] = []
    all_permissions: list[str] = []

    @classmethod
    def from_user(cls, user: "User", all_permissions: set[str]) -> "UserDetailResponse":  # noqa: F821
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=user.roles,
            direct_permissions=user.direct_permissions,
            all_permissions=sorted(all_permissions),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


# ── token schemas ─────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str