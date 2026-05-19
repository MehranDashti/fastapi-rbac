from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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


async def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")
    if sub is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(sub)

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
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None
