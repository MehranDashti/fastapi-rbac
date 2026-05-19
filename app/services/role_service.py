from typing import TYPE_CHECKING, Any

from app.core.exceptions import ConflictError, NotFoundError
from app.models.role import Role
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.services.base import BaseService

if TYPE_CHECKING:
    from app.db.pagination import PaginationParams


class RoleService(BaseService[Role]):
    def __init__(self, role_repo: RoleRepository, permission_repo: PermissionRepository) -> None:
        super().__init__(role_repo)
        self.repo: RoleRepository
        self.permission_repo = permission_repo

    async def get_by_id_with_permissions(self, role_id: int) -> Role:
        role = await self.repo.get_with_permissions(role_id)
        if not role:
            raise NotFoundError(f"Role with id {role_id} not found.")
        return role

    async def get_by_name(self, name: str, guard_name: str = "api") -> Role:
        role = await self.repo.get_by_name(name, guard_name)
        if not role:
            raise NotFoundError(f"Role '{name}' not found.")
        return role

    async def get_paginated(
        self,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_order: str,
        pagination: "PaginationParams",
    ) -> tuple[list[Role], int]:
        return await self.repo.get_filtered_paginated(filters, sort_by, sort_order, pagination)

    async def create(
        self,
        name: str,
        display_name: str,
        guard_name: str = "api",
    ) -> Role:
        if await self.repo.exists(name, guard_name):
            raise ConflictError(f"Role '{name}' already exists for guard '{guard_name}'.")
        role = Role(
            name=name,
            display_name=display_name,
            guard_name=guard_name,
        )
        return await self.repo.create(role)

    async def update(self, role_id: int, display_name: str) -> Role:
        role = await self.get_by_id(role_id)
        role.display_name = display_name
        return await self._flush_refresh(role)

    async def assign_permission(self, role_id: int, permission_id: int) -> Role:
        role = await self.get_by_id_with_permissions(role_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise NotFoundError(f"Permission with id {permission_id} not found.")
        if permission in role.permissions:
            raise ConflictError(
                f"Permission '{permission.name}' is already assigned to role '{role.name}'."
            )
        await self.repo.assign_permission(role, permission)
        return role

    async def revoke_permission(self, role_id: int, permission_id: int) -> Role:
        role = await self.get_by_id_with_permissions(role_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise NotFoundError(f"Permission with id {permission_id} not found.")
        if permission not in role.permissions:
            raise ConflictError(
                f"Permission '{permission.name}' is not assigned to role '{role.name}'."
            )
        await self.repo.revoke_permission(role, permission)
        return role
