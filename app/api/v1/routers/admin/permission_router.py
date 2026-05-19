from fastapi import APIRouter, Depends

from app.core.dependencies import get_permission_service
from app.core.permissions import require_permission
from app.core.response import created, no_content, ok
from app.db.pagination import Page, PaginationParams
from app.filters.permission_filter import PermissionFilterParams
from app.schemas.admin.permission import PermissionCreate, PermissionUpdate
from app.schemas.shared.permission import PermissionResponse
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Admin — Permissions"])


@router.get(
    "",
    summary="List permissions with filtering, sorting, and pagination",
    dependencies=[Depends(require_permission("permissions.read"))],
)
async def list_permissions(
    filters: PermissionFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    service: PermissionService = Depends(get_permission_service),
):
    items, total = await service.get_paginated(
        filters=filters.to_dict(),
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
        pagination=pagination,
    )
    page = Page.create([PermissionResponse.model_validate(p) for p in items], total, pagination)
    return ok(page)


@router.get(
    "/{permission_id}",
    summary="Get a single permission",
    dependencies=[Depends(require_permission("permissions.read"))],
)
async def get_permission(
    permission_id: int,
    service: PermissionService = Depends(get_permission_service),
):
    perm = await service.get_by_id(permission_id)
    return ok(PermissionResponse.model_validate(perm))


@router.post(
    "",
    summary="Create a permission",
    dependencies=[Depends(require_permission("permissions.create"))],
)
async def create_permission(
    body: PermissionCreate,
    service: PermissionService = Depends(get_permission_service),
):
    perm = await service.create(
        name=body.name,
        display_name=body.display_name,
        guard_name=body.guard_name,
    )
    return created(PermissionResponse.model_validate(perm))


@router.patch(
    "/{permission_id}",
    summary="Update a permission's display name",
    dependencies=[Depends(require_permission("permissions.update"))],
)
async def update_permission(
    permission_id: int,
    body: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
):
    perm = await service.update(permission_id, display_name=body.display_name)
    return ok(PermissionResponse.model_validate(perm))


@router.delete(
    "/{permission_id}",
    summary="Delete a permission",
    dependencies=[Depends(require_permission("permissions.delete"))],
)
async def delete_permission(
    permission_id: int,
    service: PermissionService = Depends(get_permission_service),
):
    await service.delete(permission_id)
    return no_content()
