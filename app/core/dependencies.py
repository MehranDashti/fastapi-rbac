"""
app/core/dependencies.py

FastAPI dependency callables shared across all routers.

Auth flow:
  1. get_current_user   — decodes JWT, loads User WITH roles + permissions from DB
  2. Permission guards  — imported from app.core.permissions, wrap get_current_user

The old CurrentAdmin / CurrentUser role-enum approach is replaced entirely by
the permission engine in app.core.permissions.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


# ── db session ────────────────────────────────────────────────────────────────

async def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


# ── service factory dependencies ──────────────────────────────────────────────

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )


async def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )


async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    return PermissionService(
        repo=PermissionRepository(db),
    )


# ── authentication ────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    1. Extract Bearer token from Authorization header.
    2. Decode and validate JWT — raises 401 on any failure.
    3. Load User from DB WITH roles and their permissions + direct permissions.
       This single DB call fully populates the user object so all downstream
       permission checks (can(), has_role(), etc.) are pure in-memory operations.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id: int | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_with_roles_and_permissions(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Same as get_current_user but returns None instead of raising 401.
    Useful for routes that behave differently for authenticated vs anonymous users.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None