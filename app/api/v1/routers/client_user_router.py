from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_user_service
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserDetailResponse,
    UserLoginRequest,
    UserSignupRequest,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def signup(
    body: UserSignupRequest,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.register(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        password=body.password,
    )
    return UserDetailResponse.from_user(user, set())


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive access + refresh tokens",
)
async def login(
    body: UserLoginRequest,
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    user = await service.authenticate(email=body.email, password=body.password)
    return TokenResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Issue a new access token using a valid refresh token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    from jose import JWTError

    try:
        payload = decode_token(body.refresh_token)
        user_id: int | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token.",
        )

    user = await service.get_by_id(user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return TokenResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (client-side token discard; server-side blacklist is a future step)",
)
async def logout(
    _: User = Depends(get_current_user),
) -> None:
    return None


@router.get(
    "/profile",
    response_model=UserDetailResponse,
    summary="Get the current user's profile with all roles and permissions",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    return UserDetailResponse.from_user(
        current_user,
        service.get_all_permissions(current_user),
    )


@router.patch(
    "/profile",
    response_model=UserDetailResponse,
    summary="Update the current user's profile",
)
async def update_profile(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.update_profile(
        user=current_user,
        full_name=body.full_name,
        password=body.password,
    )
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))