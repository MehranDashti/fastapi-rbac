from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User

from .base import BaseSeeder

SUPERADMIN_ROLE_NAME = "superadmin"


class UserSeeder(BaseSeeder):
    name = "users"
    description = "Seed first admin user and assign superadmin role"

    async def run(self, db: AsyncSession) -> None:
        email = settings.SEED_ADMIN_EMAIL
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        user = result.scalars().first()
        if not user:
            user = User(
                email=email,
                username=settings.SEED_ADMIN_USERNAME,
                full_name=settings.SEED_ADMIN_FULLNAME,
                hashed_password=get_password_hash(settings.SEED_ADMIN_PASSWORD),
                is_active=True,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)
            print(f"   ✔ created  {email}")
        else:
            print(f"   — exists   {email}")

        result = await db.execute(
            select(Role).where(Role.name == SUPERADMIN_ROLE_NAME, Role.guard_name == "api")
        )
        role = result.scalars().first()
        if role and role not in user.roles:
            user.roles.append(role)
            await db.flush()
            print(f"   ✔ assigned {SUPERADMIN_ROLE_NAME} to {email}")

        print(f"\n   Login → email: {email}  /  password: {settings.SEED_ADMIN_PASSWORD}")
        print("   Change the password immediately in production!")
