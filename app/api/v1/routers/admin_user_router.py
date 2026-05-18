from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentAdmin, DBSession
from app.db.pagination import Page, PaginationParams
from app.models.user import UserRole
from app.schemas.user import (
    AdminCreateUserRequest,
    LoginResponse,
    MessageResponse,
    UserLoginRequest,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["Admin — Users"])


def get_service(db: DBSession) -> UserService:
    return UserService(db)


@router.post("/login", response_model=LoginResponse, tags=["Admin — Auth"])
async def admin_login(
    body: UserLoginRequest,
    service: UserService = Depends(get_service),
):
    """
    Admin login — same endpoint as client login but documented separately.
    Role is validated on protected admin routes via CurrentAdmin dependency.
    """
    return await service.login(body.email, body.password)


@router.get("", response_model=Page[UserResponse])
async def list_users(
    _: CurrentAdmin,
    service: UserService = Depends(get_service),
    params: PaginationParams = Depends(),
    role: Optional[UserRole] = Query(default=None, description="Filter by role"),
):
    """Paginated list of all users. Optionally filter by role."""
    return await service.admin_list_users(params, role=role)


@router.get("/{user_id}", response_model=UserResponse)
async def view_user(
    user_id: int,
    _: CurrentAdmin,
    service: UserService = Depends(get_service),
):
    """Get a single user by ID."""
    return await service.admin_get_user(user_id)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: AdminCreateUserRequest,
    _: CurrentAdmin,
    service: UserService = Depends(get_service),
):
    """Admin creates a new user (any role)."""
    return await service.admin_create_user(body)


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    _: CurrentAdmin,
    service: UserService = Depends(get_service),
):
    """Activate or deactivate a user account."""
    return await service.admin_toggle_active(user_id)