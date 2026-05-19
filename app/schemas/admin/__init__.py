from app.schemas.admin.permission import PermissionCreate, PermissionUpdate
from app.schemas.admin.role import (
    AssignPermissionRequest,
    AssignPermissionsRequest,
    RoleCreate,
    RoleUpdate,
)
from app.schemas.admin.user import (
    AdminUserCreateRequest,
    AssignDirectPermissionRequest,
    AssignDirectPermissionsRequest,
    AssignRoleRequest,
    AssignRolesRequest,
)

__all__ = [
    "PermissionCreate",
    "PermissionUpdate",
    "RoleCreate",
    "RoleUpdate",
    "AssignPermissionRequest",
    "AssignPermissionsRequest",
    "AdminUserCreateRequest",
    "AssignRoleRequest",
    "AssignRolesRequest",
    "AssignDirectPermissionRequest",
    "AssignDirectPermissionsRequest",
]
