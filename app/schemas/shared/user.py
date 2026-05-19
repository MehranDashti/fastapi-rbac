from datetime import datetime

from pydantic import BaseModel

from app.schemas.shared.permission import PermissionResponse
from app.schemas.shared.role import RoleDetailResponse


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
