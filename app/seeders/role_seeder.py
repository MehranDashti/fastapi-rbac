from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role

from .base import BaseSeeder
from .permission_seeder import SYSTEM_PERMISSIONS

SUPERADMIN_ROLE = ("superadmin", "Super Administrator")


class RoleSeeder(BaseSeeder):
    name = "roles"
    description = "Seed superadmin role and assign all system permissions"

    async def run(self, db: AsyncSession) -> None:
        role_name, role_display = SUPERADMIN_ROLE
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == role_name, Role.guard_name == "api")
        )
        role = result.scalars().first()
        if not role:
            role = Role(name=role_name, display_name=role_display, guard_name="api")
            db.add(role)
            await db.flush()
            await db.refresh(role)
            print(f"   ✔ created  {role_name}")
        else:
            print(f"   — exists   {role_name}")

        perm_names = [name for name, _ in SYSTEM_PERMISSIONS]
        result = await db.execute(
            select(Permission).where(
                Permission.name.in_(perm_names),
                Permission.guard_name == "api",
            )
        )
        perms = result.scalars().all()
        for perm in perms:
            if perm not in role.permissions:
                role.permissions.append(perm)
        await db.flush()
        print(f"   ✔ {len(perms)} permissions assigned to {role_name}")
