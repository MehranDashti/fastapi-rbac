from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_role_service
from app.core.permissions import require_permission
from app.schemas.role import (
    AssignPermissionRequest,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
)
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Admin — Roles"])


@router.get(
    "",
    response_model=list[RoleResponse],
    summary="List all roles",
    dependencies=[Depends(require_permission("roles.read"))],
)
async def list_roles(
    service: RoleService = Depends(get_role_service),
) -> list[RoleResponse]:
    return await service.get_all()


@router.get(
    "/{role_id}",
    response_model=RoleDetailResponse,
    summary="Get a role with its permissions",
    dependencies=[Depends(require_permission("roles.read"))],
)
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await service.get_by_id_with_permissions(role_id)


@router.post(
    "",
    response_model=RoleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a role",
    dependencies=[Depends(require_permission("roles.create"))],
)
async def create_role(
    body: RoleCreate,
    service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await service.create(
        name=body.name,
        display_name=body.display_name,
        guard_name=body.guard_name,
    )


@router.patch(
    "/{role_id}",
    response_model=RoleDetailResponse,
    summary="Update a role's display name",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def update_role(
    role_id: int,
    body: RoleUpdate,
    service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await service.update(role_id, display_name=body.display_name)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    dependencies=[Depends(require_permission("roles.delete"))],
)
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
) -> None:
    await service.delete(role_id)



@router.post(
    "/{role_id}/permissions",
    response_model=RoleDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a permission to a role",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def assign_permission_to_role(
    role_id: int,
    body: AssignPermissionRequest,
    service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await service.assign_permission(role_id, body.permission_id)


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a permission from a role",
    dependencies=[Depends(require_permission("roles.update"))],
)
async def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await service.revoke_permission(role_id, permission_id)