from collections.abc import Callable

from fastapi import Depends, HTTPException, status

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


def require_permission(*permissions: str) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_all(current_user, *permissions):
            missing = [p for p in permissions if not can(current_user, p)]
            raise PermissionDeniedError(
                detail=f"Missing required permission(s): {', '.join(missing)}."
            )
        return current_user
    dependency.__name__ = f"require_permission({'|'.join(permissions)})"
    return dependency


def require_any_permission(*permissions: str) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_any(current_user, *permissions):
            raise PermissionDeniedError(
                detail=f"Requires at least one of: {', '.join(permissions)}."
            )
        return current_user
    dependency.__name__ = f"require_any_permission({'|'.join(permissions)})"
    return dependency


def require_all_permissions(*permissions: str) -> Callable:
    return require_permission(*permissions)


def require_role(*roles: str) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_all_roles(current_user, *roles):
            missing = [r for r in roles if not has_role(current_user, r)]
            raise PermissionDeniedError(
                detail=f"Missing required role(s): {', '.join(missing)}."
            )
        return current_user
    dependency.__name__ = f"require_role({'|'.join(roles)})"
    return dependency


def require_any_role(*roles: str) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_any_role(current_user, *roles):
            raise PermissionDeniedError(
                detail=f"Requires at least one of these roles: {', '.join(roles)}."
            )
        return current_user
    dependency.__name__ = f"require_any_role({'|'.join(roles)})"
    return dependency


def require_active_user() -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise PermissionDeniedError(detail="Your account is inactive.")
        return current_user
    return dependency
