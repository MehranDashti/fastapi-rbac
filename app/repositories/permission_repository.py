from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_role_permission import Permission

from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.db.pagination import PaginationParams


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)

    async def get_by_name(self, name: str, guard_name: str = "api") -> Permission | None:
        result = await self.db.execute(
            select(Permission).where(
                Permission.name == name,
                Permission.guard_name == guard_name,
            )
        )
        return result.scalars().first()

    async def get_all_by_guard(self, guard_name: str = "api") -> list[Permission]:
        result = await self.db.execute(
            select(Permission).where(Permission.guard_name == guard_name)
        )
        return list(result.scalars().all())

    async def exists(self, name: str, guard_name: str = "api") -> bool:
        result = await self.db.execute(
            select(Permission.id).where(
                Permission.name == name,
                Permission.guard_name == guard_name,
            )
        )
        return result.scalars().first() is not None

    async def get_filtered_paginated(
        self,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_order: str,
        pagination: "PaginationParams",
    ) -> tuple[list[Permission], int]:
        from app.filters.permission_filter import PermissionFilter
        f = PermissionFilter()
        query = f.apply(select(Permission), filters)
        query = f.apply_sort(query, Permission, sort_by, sort_order)
        return await self._paginate(query, pagination)