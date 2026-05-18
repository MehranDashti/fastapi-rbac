from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.user import (
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Client — Auth & Profile"])


def get_service(db: DBSession) -> UserService:
    return UserService(db)


@router.post("/signup", response_model=LoginResponse, status_code=201)
async def signup(
    body: UserSignupRequest,
    service: UserService = Depends(get_service),
):
    """Register a new client account."""
    return await service.signup(body)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: UserLoginRequest,
    service: UserService = Depends(get_service),
):
    """Login and receive access + refresh tokens."""
    return await service.login(body.email, body.password)


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: CurrentUser):
    """
    Logout endpoint.
    Tokens are stateless JWTs — invalidation is handled client-side by
    discarding the token. For server-side revocation add a token blacklist
    (Redis) here.
    """
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_service),
):
    """Get a new access token using a valid refresh token."""
    return await service.refresh_tokens(body.refresh_token)


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: CurrentUser):
    """Get the authenticated user's profile."""
    from app.schemas.user import UserResponse
    return UserResponse.model_validate(current_user)


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    body: UserUpdateRequest,
    current_user: CurrentUser,
    service: UserService = Depends(get_service),
):
    """Update the authenticated user's profile."""
    return await service.update_profile(current_user, body)