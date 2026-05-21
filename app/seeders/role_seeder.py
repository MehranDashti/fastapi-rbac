from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_role_permission import Permission, Role
from fastapi_role_permission.exceptions import RoleDoesNotExist

from .base import BaseSeeder
from .permission_seeder import SYSTEM_PERMISSIONS

SUPERADMIN_ROLE = "superadmin"


class RoleSeeder(BaseSeeder):
    name = "roles"
    description = "Seed superadmin role and assign all system permissions"

    async def run(self, db: AsyncSession) -> None:
        try:
            role = await Role.find_by_name(db, SUPERADMIN_ROLE, guard_name="api")
            print(f"   — exists   {SUPERADMIN_ROLE}")
        except RoleDoesNotExist:
            role = await Role.create(db, SUPERADMIN_ROLE, guard_name="api")
            print(f"   ✔ created  {SUPERADMIN_ROLE}")

        result = await db.execute(
            select(Permission).where(
                Permission.name.in_(SYSTEM_PERMISSIONS),
                Permission.guard_name == "api",
            )
        )
        perms = list(result.scalars().all())
        for perm in perms:
            if perm not in role.permissions:
                role.permissions.append(perm)
        await db.flush()
        print(f"   ✔ {len(perms)} permissions assigned to {SUPERADMIN_ROLE}")
