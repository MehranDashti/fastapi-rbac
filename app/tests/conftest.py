import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers both Base and RBACBase tables
from app.core.security import get_password_hash
from app.db.session import Base, get_db
from fastapi_role_permission import Permission, PermissionConfig, Role, init_rbac
from fastapi_role_permission.models.base import RBACBase
from app.models.user import User
from app.tests.factories import make_user
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

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


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    from app.core.dependencies import get_current_user
    # Call init_rbac once per test session so mixin methods (assign_role etc.)
    # work in unit tests that use db_session directly (no client/lifespan involved).
    init_rbac(
        app,
        get_db=get_db,
        get_current_user=get_current_user,
        user_model=User,
        config=PermissionConfig(guard_name="api"),
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(RBACBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(RBACBase.metadata.drop_all)
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(RBACBase.metadata.sorted_tables):
            await conn.execute(table.delete())
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    async with TestSessionLocal() as db:
        perms: list[Permission] = []
        for name in SYSTEM_PERMISSIONS:
            perm = Permission(name=name, guard_name="api")
            db.add(perm)
            perms.append(perm)
        await db.flush()

        role = Role(name="superadmin", guard_name="api")
        db.add(role)
        await db.flush()
        await db.refresh(role)
        role.permissions.extend(perms)
        await db.flush()

        user = User(
            email="admin@test.com",
            username="admin",
            full_name="Test Admin",
            hashed_password=get_password_hash("Admin1234"),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        # user.roles is viewonly — use mixin method (init_rbac is called via lifespan on client)
        await user.assign_role(db, role)
        await db.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin1234"},
    )
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/signup", json={
        "email": "user@test.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "Password1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "Password1",
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
