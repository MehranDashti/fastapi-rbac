from fastapi import APIRouter, Depends

from app.core.dependencies import get_user_service
from app.core.permissions import require_permission
from app.core.response import created, ok
from app.db.pagination import Page, PaginationParams
from app.filters.user_filter import UserFilterParams
from app.schemas.admin.user import (
    AdminUserCreateRequest,
    AssignDirectPermissionRequest,
    AssignRoleRequest,
)
from app.schemas.shared.user import UserDetailResponse, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Admin — Users"])


@router.get(
    "",
    summary="List users with filtering, sorting, and pagination",
    dependencies=[Depends(require_permission("users.read"))],
)
async def list_users(
    filters: UserFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
):
    items, total = await service.get_paginated(
        filters=filters.to_dict(),
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
        pagination=pagination,
    )
    page = Page.create([UserResponse.model_validate(u) for u in items], total, pagination)
    return ok(page)


@router.get(
    "/{user_id}",
    summary="Get a single user with roles, permissions",
    dependencies=[Depends(require_permission("users.read"))],
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    user = await service.get_by_id_with_roles_and_permissions(user_id)
    return ok(UserDetailResponse.from_user(user, service.get_all_permissions(user)))


@router.post(
    "",
    summary="Create a user (optionally assign roles immediately)",
    dependencies=[Depends(require_permission("users.create"))],
)
async def create_user(
    body: AdminUserCreateRequest,
    service: UserService = Depends(get_user_service),
):
    user = await service.register(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        password=body.password,
    )
    if body.role_ids:
        user = await service.sync_roles(user.id, body.role_ids)
    user = await service.get_by_id_with_roles_and_permissions(user.id)
    return created(UserDetailResponse.from_user(user, service.get_all_permissions(user)))


@router.patch(
    "/{user_id}/toggle-active",
    summary="Toggle user active/inactive status",
    dependencies=[Depends(require_permission("users.update"))],
)
async def toggle_user_active(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    user = await service.toggle_active(user_id)
    return ok(UserResponse.model_validate(user))


@router.post(
    "/{user_id}/roles",
    summary="Assign a role to a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def assign_role_to_user(
    user_id: int,
    body: AssignRoleRequest,
    service: UserService = Depends(get_user_service),
):
    user = await service.assign_role(user_id, body.role_id)
    return ok(UserDetailResponse.from_user(user, service.get_all_permissions(user)))


@router.delete(
    "/{user_id}/roles/{role_id}",
    summary="Revoke a role from a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    service: UserService = Depends(get_user_service),
):
    user = await service.revoke_role(user_id, role_id)
    return ok(UserDetailResponse.from_user(user, service.get_all_permissions(user)))


@router.post(
    "/{user_id}/permissions",
    summary="Assign a direct permission to a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def assign_direct_permission_to_user(
    user_id: int,
    body: AssignDirectPermissionRequest,
    service: UserService = Depends(get_user_service),
):
    user = await service.assign_direct_permission(user_id, body.permission_id)
    return ok(UserDetailResponse.from_user(user, service.get_all_permissions(user)))


@router.delete(
    "/{user_id}/permissions/{permission_id}",
    summary="Revoke a direct permission from a user",
    dependencies=[Depends(require_permission("users.update"))],
)
async def revoke_direct_permission_from_user(
    user_id: int,
    permission_id: int,
    service: UserService = Depends(get_user_service),
):
    user = await service.revoke_direct_permission(user_id, permission_id)
    return ok(UserDetailResponse.from_user(user, service.get_all_permissions(user)))
