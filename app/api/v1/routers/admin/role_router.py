from fastapi import APIRouter, Depends

from app.core.dependencies import get_role_service
from app.core.permissions import require_permission
from app.core.response import created, no_content, ok
from app.db.pagination import Page, PaginationParams
from app.filters.role_filter import RoleFilterParams
from app.schemas.admin.role import AssignPermissionRequest, RoleCreate, RoleUpdate
from app.schemas.shared.role import RoleDetailResponse, RoleResponse
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Admin — Roles"])


@router.get(
    "",
    summary="List roles with filtering, sorting, and pagination",
    dependencies=[Depends(require_permission("roles.read"))],
)
async def list_roles(
    filters: RoleFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    service: RoleService = Depends(get_role_service),
):
    items, total = await service.get_paginated(
        filters=filters.to_dict(),
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
        pagination=pagination,
    )
    page = Page.create([RoleResponse.model_validate(r) for r in items], total, pagination)
    return ok(page)


@router.get(
    "/{role_id}",
    summary="Get a role with its permissions",
    dependencies=[Depends(require_permission("roles.read"))],
)
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
):
    role = await service.get_by_id_with_permissions(role_id)
    return ok(RoleDetailResponse.model_validate(role))


@router.post(
    "",
    summary="Create a role",
    dependencies=[Depends(require_permission("roles.create"))],
)
async def create_role(
    body: RoleCreate,
    service: RoleService = Depends(get_role_service),
):
    role = await service.create(
        name=body.name,
        display_name=body.display_name,
        guard_name=body.guard_name,
    )
    return created(RoleDetailResponse.model_validate(role))


@router.patch(
    "/{role_id}",
    summary="Update a role's display name",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def update_role(
    role_id: int,
    body: RoleUpdate,
    service: RoleService = Depends(get_role_service),
):
    role = await service.update(role_id, display_name=body.display_name)
    return ok(RoleDetailResponse.model_validate(role))


@router.delete(
    "/{role_id}",
    summary="Delete a role",
    dependencies=[Depends(require_permission("roles.delete"))],
)
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
):
    await service.delete(role_id)
    return no_content()


@router.post(
    "/{role_id}/permissions",
    summary="Assign a permission to a role",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def assign_permission_to_role(
    role_id: int,
    body: AssignPermissionRequest,
    service: RoleService = Depends(get_role_service),
):
    role = await service.assign_permission(role_id, body.permission_id)
    return ok(RoleDetailResponse.model_validate(role))


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    summary="Revoke a permission from a role",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    service: RoleService = Depends(get_role_service),
):
    role = await service.revoke_permission(role_id, permission_id)
    return ok(RoleDetailResponse.model_validate(role))
