from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_active_users_query(self):
        """Returns a composable select() for use with paginate()."""
        return select(User).where(User.is_active == True).order_by(User.created_at.desc())

    async def get_all_users_query(self, role: Optional[UserRole] = None):
        """Admin: all users query, optionally filtered by role."""
        q = select(User).order_by(User.created_at.desc())
        if role:
            q = q.where(User.role == role)
        return q

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def username_exists(self, username: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None