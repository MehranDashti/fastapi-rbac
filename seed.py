import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

from app.core.config import settings  # noqa: E402

DATABASE_URL: str = settings.DATABASE_URL

FIRST_ADMIN = {
    "email":     settings.SEED_ADMIN_EMAIL,
    "username":  settings.SEED_ADMIN_USERNAME,
    "full_name": settings.SEED_ADMIN_FULLNAME,
    "password":  settings.SEED_ADMIN_PASSWORD,
}

SYSTEM_PERMISSIONS: list[tuple[str, str]] = [
    ("users.read",              "Read Users"),
    ("users.create",            "Create Users"),
    ("users.update",            "Update Users"),
    ("users.delete",            "Delete Users"),
    ("roles.read",              "Read Roles"),
    ("roles.create",            "Create Roles"),
    ("roles.update",            "Update Roles"),
    ("roles.delete",            "Delete Roles"),
    ("permissions.read",        "Read Permissions"),
    ("permissions.create",      "Create Permissions"),
    ("permissions.update",      "Update Permissions"),
    ("permissions.delete",      "Delete Permissions"),
]

SUPERADMIN_ROLE = ("superadmin", "Super Administrator")


async def seed() -> None:
    import app.models  # noqa: F401
    from app.core.security import get_password_hash
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.user import User

    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as db:
        async with db.begin():
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            print("→ Seeding permissions...")
            permissions: dict[str, Permission] = {}
            for name, display_name in SYSTEM_PERMISSIONS:
                result = await db.execute(
                    select(Permission).where(
                        Permission.name == name,
                        Permission.guard_name == "api",
                    )
                )
                perm = result.scalars().first()
                if not perm:
                    perm = Permission(name=name, display_name=display_name, guard_name="api")
                    db.add(perm)
                    await db.flush()
                    print(f"   ✔ created  {name}")
                elif perm.display_name != display_name:
                    perm.display_name = display_name
                    await db.flush()
                    print(f"   ↻ updated  {name}")
                else:
                    print(f"   — exists   {name}")
                permissions[name] = perm

            print("→ Seeding superadmin role...")
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
                print(f"   ✔ created  {role_name}")
            else:
                print(f"   — exists   {role_name}")

            for perm in permissions.values():
                if perm not in role.permissions:
                    role.permissions.append(perm)
            await db.flush()
            print(f"   ✔ {len(permissions)} permissions assigned to {role_name}")

            print("→ Seeding first admin user...")
            result = await db.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.email == FIRST_ADMIN["email"])
            )
            user = result.scalars().first()
            if not user:
                user = User(
                    email=FIRST_ADMIN["email"],
                    username=FIRST_ADMIN["username"],
                    full_name=FIRST_ADMIN["full_name"],
                    hashed_password=get_password_hash(FIRST_ADMIN["password"]),
                    is_active=True,
                )
                db.add(user)
                await db.flush()
                print(f"   ✔ created  {FIRST_ADMIN['email']}")
            else:
                print(f"   — exists   {FIRST_ADMIN['email']}")

            if role not in user.roles:
                user.roles.append(role)
                await db.flush()
                print(f"   ✔ assigned {role_name} role to {FIRST_ADMIN['email']}")

    await engine.dispose()
    print("\n✅ Seed complete.")
    print(f"   Login → email: {FIRST_ADMIN['email']}  /  password: {FIRST_ADMIN['password']}")
    print("   Change the password immediately in production!\n")


if __name__ == "__main__":
    asyncio.run(seed())
