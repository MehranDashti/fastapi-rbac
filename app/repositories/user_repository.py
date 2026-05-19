from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    # ── lookups ───────────────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get_with_roles_and_permissions(self, user_id: int) -> User | None:
        """
        Load user with roles (and each role's permissions) + direct permissions
        in a single round-trip using nested selectinload.
        This is the method used by the auth dependency so every request has a
        fully populated user object ready for permission checks.
        """
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.direct_permissions),
            )
            .where(User.id == user_id)
        )
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalars().first() is not None

    async def username_exists(self, username: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalars().first() is not None

    # ── role assignment ───────────────────────────────────────────────────────

    async def assign_role(self, user: User, role: Role) -> None:
        """Attach a role to a user (idempotent)."""
        if role not in user.roles:
            user.roles.append(role)
            await self.db.flush()

    async def revoke_role(self, user: User, role: Role) -> None:
        """Detach a role from a user (idempotent)."""
        if role in user.roles:
            user.roles.remove(role)
            await self.db.flush()

    async def sync_roles(self, user: User, roles: list[Role]) -> None:
        """Replace the user's entire role set with the provided list."""
        user.roles = roles
        await self.db.flush()

    # ── direct permission assignment ──────────────────────────────────────────

    async def assign_direct_permission(self, user: User, permission: Permission) -> None:
        """Attach a permission directly to a user, bypassing roles (idempotent)."""
        if permission not in user.direct_permissions:
            user.direct_permissions.append(permission)
            await self.db.flush()

    async def revoke_direct_permission(self, user: User, permission: Permission) -> None:
        """Detach a direct permission from a user (idempotent)."""
        if permission in user.direct_permissions:
            user.direct_permissions.remove(permission)
            await self.db.flush()

    async def sync_direct_permissions(self, user: User, permissions: list[Permission]) -> None:
        """Replace the user's entire direct-permission set with the provided list."""
        user.direct_permissions = permissions
        await self.db.flush()