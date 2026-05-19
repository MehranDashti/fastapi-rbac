from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_user_service
from app.core.permissions import require_permission
from app.schemas.user import (
    AdminUserCreateRequest,
    AssignDirectPermissionRequest,
    AssignRoleRequest,
    UserDetailResponse,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Admin — Users"])


# ── user CRUD ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users",
    dependencies=[Depends(require_permission("users.read"))],
)
async def list_users(
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    return await service.get_all()


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get a single user with roles, permissions",
    dependencies=[Depends(require_permission("users.read"))],
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.get_by_id_with_roles_and_permissions(user_id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (optionally assign roles immediately)",
    dependencies=[Depends(require_permission("users.create"))],
)
async def create_user(
    body: AdminUserCreateRequest,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.register(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        password=body.password,
    )
    # assign roles if provided in the request body
    if body.role_ids:
        user = await service.sync_roles(user.id, body.role_ids)
    user = await service.get_by_id_with_roles_and_permissions(user.id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))


@router.patch(
    "/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Toggle user active/inactive status",
    dependencies=[Depends(require_permission("users.update"))],
)
async def toggle_user_active(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.toggle_active(user_id)


# ── role assignment ───────────────────────────────────────────────────────────

@router.post(
    "/{user_id}/roles",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a role to a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def assign_role_to_user(
    user_id: int,
    body: AssignRoleRequest,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.assign_role(user_id, body.role_id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a role from a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.revoke_role(user_id, role_id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))


# ── direct permission assignment ──────────────────────────────────────────────

@router.post(
    "/{user_id}/permissions",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a direct permission to a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def assign_direct_permission_to_user(
    user_id: int,
    body: AssignDirectPermissionRequest,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.assign_direct_permission(user_id, body.permission_id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))


@router.delete(
    "/{user_id}/permissions/{permission_id}",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a direct permission from a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def revoke_direct_permission_from_user(
    user_id: int,
    permission_id: int,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    user = await service.revoke_direct_permission(user_id, permission_id)
    return UserDetailResponse.from_user(user, service.get_all_permissions(user))