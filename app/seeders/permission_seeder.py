from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission

from .base import BaseSeeder

SYSTEM_PERMISSIONS: list[tuple[str, str]] = [
    ("users.read",         "Read Users"),
    ("users.create",       "Create Users"),
    ("users.update",       "Update Users"),
    ("users.delete",       "Delete Users"),
    ("roles.read",         "Read Roles"),
    ("roles.create",       "Create Roles"),
    ("roles.update",       "Update Roles"),
    ("roles.delete",       "Delete Roles"),
    ("permissions.read",   "Read Permissions"),
    ("permissions.create", "Create Permissions"),
    ("permissions.update", "Update Permissions"),
    ("permissions.delete", "Delete Permissions"),
]


class PermissionSeeder(BaseSeeder):
    name = "permissions"
    description = "Seed 12 system permissions"

    async def run(self, db: AsyncSession) -> None:
        for perm_name, display_name in SYSTEM_PERMISSIONS:
            result = await db.execute(
                select(Permission).where(
                    Permission.name == perm_name,
                    Permission.guard_name == "api",
                )
            )
            perm = result.scalars().first()
            if not perm:
                db.add(Permission(name=perm_name, display_name=display_name, guard_name="api"))
                await db.flush()
                print(f"   ✔ created  {perm_name}")
            elif perm.display_name != display_name:
                perm.display_name = display_name
                await db.flush()
                print(f"   ↻ updated  {perm_name}")
            else:
                print(f"   — exists   {perm_name}")
