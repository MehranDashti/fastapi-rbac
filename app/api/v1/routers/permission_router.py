from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_permission_service
from app.core.permissions import require_permission
from app.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Admin — Permissions"])


@router.get(
    "",
    response_model=list[PermissionResponse],
    summary="List all permissions",
    dependencies=[Depends(require_permission("permissions.read"))],
)
async def list_permissions(
    guard_name: str = "api",
    service: PermissionService = Depends(get_permission_service),
) -> list[PermissionResponse]:
    return await service.get_all(guard_name)


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    summary="Get a single permission",
    dependencies=[Depends(require_permission("permissions.read"))],
)
async def get_permission(
    permission_id: int,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    return await service.get_by_id(permission_id)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a permission",
    dependencies=[Depends(require_permission("permissions.create"))],
)
async def create_permission(
    body: PermissionCreate,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    return await service.create(
        name=body.name,
        display_name=body.display_name,
        guard_name=body.guard_name,
    )


@router.patch(
    "/{permission_id}",
    response_model=PermissionResponse,
    summary="Update a permission's display name",
    dependencies=[Depends(require_permission("permissions.update"))],
)
async def update_permission(
    permission_id: int,
    body: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    return await service.update(permission_id, display_name=body.display_name)


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a permission",
    dependencies=[Depends(require_permission("permissions.delete"))],
)
async def delete_permission(
    permission_id: int,
    service: PermissionService = Depends(get_permission_service),
) -> None:
    await service.delete(permission_id)