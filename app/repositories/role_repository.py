from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role
from app.repositories.base import BaseRepository


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