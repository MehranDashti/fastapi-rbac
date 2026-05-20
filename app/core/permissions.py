from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from fastapi_role_permission import (
    require_permission,
    require_any_permission,
    require_role,
    require_any_role,
    require_role_or_permission,
)

from app.core.dependencies import get_current_user
from app.models.user import User


class PermissionDeniedError(HTTPException):
    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotAuthenticatedError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_all_permissions(user: User) -> set[str]:
    from_roles: set[str] = {
        perm.name
        for role in user.roles
        for perm in role.permissions
    }
    direct: set[str] = {perm.name for perm in user.direct_permissions}
    return from_roles | direct


def can(user: User, permission: str) -> bool:
    return permission in get_all_permissions(user)


def can_any(user: User, *permissions: str) -> bool:
    all_perms = get_all_permissions(user)
    return any(p in all_perms for p in permissions)


def can_all(user: User, *permissions: str) -> bool:
    all_perms = get_all_permissions(user)
    return all(p in all_perms for p in permissions)


def has_role(user: User, role: str) -> bool:
    return any(r.name == role for r in user.roles)


def has_any_role(user: User, *roles: str) -> bool:
    user_role_names = {r.name for r in user.roles}
    return any(r in user_role_names for r in roles)


def has_all_roles(user: User, *roles: str) -> bool:
    user_role_names = {r.name for r in user.roles}
    return all(r in user_role_names for r in roles)


# Package's require_* are re-exported here so all route imports stay the same.
# require_permission, require_any_permission, require_role, require_any_role,
# require_role_or_permission are all imported above.

def require_all_permissions(*permissions: str) -> Callable:
    return require_permission(*permissions)


def require_active_user() -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise PermissionDeniedError(detail="Your account is inactive.")
        return current_user
    return dependency
