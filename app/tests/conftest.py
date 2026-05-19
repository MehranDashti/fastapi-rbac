import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.security import get_password_hash
from app.db.session import Base, get_db
from app.models.permission import Permission
from app.models.role import Role
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

SYSTEM_PERMISSIONS: list[tuple[str, str]] = [
    ("users.read",          "Read Users"),
    ("users.create",        "Create Users"),
    ("users.update",        "Update Users"),
    ("users.delete",        "Delete Users"),
    ("roles.read",          "Read Roles"),
    ("roles.create",        "Create Roles"),
    ("roles.update",        "Update Roles"),
    ("roles.delete",        "Delete Roles"),
    ("permissions.read",    "Read Permissions"),
    ("permissions.create",  "Create Permissions"),
    ("permissions.update",  "Update Permissions"),
    ("permissions.delete",  "Delete Permissions"),
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
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with test_engine.begin() as conn:
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
        for name, display_name in SYSTEM_PERMISSIONS:
            perm = Permission(name=name, display_name=display_name, guard_name="api")
            db.add(perm)
            perms.append(perm)
        await db.flush()

        role = Role(name="superadmin", display_name="Super Admin", guard_name="api")
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
        user.roles.append(role)
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
