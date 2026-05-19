from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository
from app.services.base import BaseService

if TYPE_CHECKING:
    from app.db.pagination import PaginationParams


class PermissionService(BaseService[Permission]):
    def __init__(self, repo: PermissionRepository) -> None:
        super().__init__(repo)
        self.repo: PermissionRepository

    async def get_all(self, guard_name: str = "api") -> list[Permission]:  # type: ignore[override]
        return await self.repo.get_all_by_guard(guard_name)

    async def get_paginated(
        self,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_order: str,
        pagination: "PaginationParams",
    ) -> tuple[list[Permission], int]:
        return await self.repo.get_filtered_paginated(filters, sort_by, sort_order, pagination)

    async def get_by_name(self, name: str, guard_name: str = "api") -> Permission:
        permission = await self.repo.get_by_name(name, guard_name)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{name}' not found.",
            )
        return permission

    async def create(
        self,
        name: str,
        display_name: str,
        guard_name: str = "api",
    ) -> Permission:
        if await self.repo.exists(name, guard_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{name}' already exists for guard '{guard_name}'.",
            )
        permission = Permission(
            name=name,
            display_name=display_name,
            guard_name=guard_name,
        )
        return await self.repo.create(permission)

    async def update(self, permission_id: int, display_name: str) -> Permission:
        permission = await self.get_by_id(permission_id)
        permission.display_name = display_name
        return await self._flush_refresh(permission)
