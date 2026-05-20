from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_role_permission import Permission, Role

from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.db.pagination import PaginationParams


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Role, db)

    async def get_by_name(self, name: str, guard_name: str = "api") -> Role | None:
        result = await self.db.execute(
            select(Role).where(
                Role.name == name,
                Role.guard_name == guard_name,
            )
        )
        return result.scalars().first()

    async def get_with_permissions(self, role_id: int) -> Role | None:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalars().first()

    async def exists(self, name: str, guard_name: str = "api") -> bool:
        result = await self.db.execute(
            select(Role.id).where(
                Role.name == name,
                Role.guard_name == guard_name,
            )
        )
        return result.scalars().first() is not None

    async def assign_permission(self, role: Role, permission: Permission) -> None:
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.flush()

    async def revoke_permission(self, role: Role, permission: Permission) -> None:
        if permission in role.permissions:
            role.permissions.remove(permission)
            await self.db.flush()

    async def get_filtered_paginated(
        self,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_order: str,
        pagination: "PaginationParams",
    ) -> tuple[list[Role], int]:
        from app.filters.role_filter import RoleFilter
        f = RoleFilter()
        query = f.apply(select(Role), filters)
        query = f.apply_sort(query, Role, sort_by, sort_order)
        return await self._paginate(query, pagination)