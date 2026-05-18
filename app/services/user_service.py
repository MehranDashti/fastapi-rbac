from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.pagination import Page, PaginationParams, paginate
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    AdminCreateUserRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    UserSignupRequest,
    UserUpdateRequest,
)


def _make_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            subject=str(user.id), extra={"role": user.role}
        ),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def signup(self, data: UserSignupRequest) -> LoginResponse:
        if await self.repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        if await self.repo.username_exists(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=UserRole.CLIENT,
        )
        user = await self.repo.create(user)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=_make_tokens(user),
        )

    async def login(self, email: str, password: str) -> LoginResponse:
        user = await self.repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=_make_tokens(user),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = await self.repo.get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return _make_tokens(user)

    # ── Client profile ────────────────────────────────────────────────────────

    async def get_profile(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def update_profile(
        self, user: User, data: UserUpdateRequest
    ) -> UserResponse:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.username is not None:
            if await self.repo.username_exists(data.username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken",
                )
            user.username = data.username

        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    # ── Admin ─────────────────────────────────────────────────────────────────

    async def admin_list_users(
        self,
        params: PaginationParams,
        role: Optional[UserRole] = None,
    ) -> Page[UserResponse]:
        query = await self.repo.get_all_users_query(role=role)
        items, total = await paginate(self.db, query, params)
        responses = [UserResponse.model_validate(u) for u in items]
        return Page.create(responses, total, params)

    async def admin_get_user(self, user_id: int) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserResponse.model_validate(user)

    async def admin_create_user(self, data: AdminCreateUserRequest) -> UserResponse:
        if await self.repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        if await self.repo.username_exists(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
        )
        user = await self.repo.create(user)
        return UserResponse.model_validate(user)

    async def admin_toggle_active(self, user_id: int) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        user.is_active = not user.is_active
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)