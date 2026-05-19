"""
app/core/permissions.py

The permission engine — mirrors Spatie's can() / hasPermissionTo() / hasRole() API
but as FastAPI dependency factories.

Usage on routes:

    # single permission required
    @router.get("/users", dependencies=[Depends(require_permission("users.read"))])

    # any one of these permissions is enough
    @router.delete("/users/{id}", dependencies=[Depends(require_any_permission("users.delete", "admin.all"))])

    # user must hold ALL of these permissions
    @router.post("/publish", dependencies=[Depends(require_all_permissions("posts.create", "posts.publish"))])

    # role-based guard
    @router.get("/dashboard", dependencies=[Depends(require_role("admin"))])

    # any one of these roles
    @router.get("/reports", dependencies=[Depends(require_any_role("admin", "manager"))])

    # access user object AND check permission in the same route
    async def my_route(user: User = Depends(get_current_user)):
        if not can(user, "orders.refund"):
            raise PermissionDeniedError()
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User


# ── errors ────────────────────────────────────────────────────────────────────

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


# ── pure resolution helpers (no FastAPI, fully testable) ─────────────────────

def get_all_permissions(user: User) -> set[str]:
    """
    Union of every permission the user holds:
      - permissions inherited via assigned roles
      - permissions directly granted to the user
    """
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


# ── dependency factories ──────────────────────────────────────────────────────
#
# Each factory returns a FastAPI-compatible async callable.
# The returned callable takes `current_user` via Depends(get_current_user)
# so the auth check (JWT decode + DB load) happens automatically before
# the permission check.

def require_permission(*permissions: str) -> Callable:
    """
    All listed permissions are required (AND logic).
    For OR logic use require_any_permission().
    """
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
    """At least one of the listed permissions is required (OR logic)."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_any(current_user, *permissions):
            raise PermissionDeniedError(
                detail=f"Requires at least one of: {', '.join(permissions)}."
            )
        return current_user
    dependency.__name__ = f"require_any_permission({'|'.join(permissions)})"
    return dependency


def require_all_permissions(*permissions: str) -> Callable:
    """Explicit alias for require_permission() — all permissions required (AND logic)."""
    return require_permission(*permissions)


def require_role(*roles: str) -> Callable:
    """All listed roles are required (AND logic)."""
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
    """At least one of the listed roles is required (OR logic)."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_any_role(current_user, *roles):
            raise PermissionDeniedError(
                detail=f"Requires at least one of these roles: {', '.join(roles)}."
            )
        return current_user
    dependency.__name__ = f"require_any_role({'|'.join(roles)})"
    return dependency


def require_active_user() -> Callable:
    """Ensures the authenticated user's account is active."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise PermissionDeniedError(detail="Your account is inactive.")
        return current_user
    return dependency