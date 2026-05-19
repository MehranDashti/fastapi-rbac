from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.repositories.base import BaseRepository


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