from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_role_permission import Permission

from .base import BaseSeeder

SYSTEM_PERMISSIONS: list[str] = [
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
    "roles.read",
    "roles.create",
    "roles.update",
    "roles.delete",
    "permissions.read",
    "permissions.create",
    "permissions.update",
    "permissions.delete",
]


class PermissionSeeder(BaseSeeder):
    name = "permissions"
    description = "Seed 12 system permissions"

    async def run(self, db: AsyncSession) -> None:
        for perm_name in SYSTEM_PERMISSIONS:
            perm = await Permission.find_by_name(db, perm_name, guard_name="api")
            if not perm:
                await Permission.create(db, perm_name, guard_name="api")
                print(f"   ✔ created  {perm_name}")
            else:
                print(f"   — exists   {perm_name}")
