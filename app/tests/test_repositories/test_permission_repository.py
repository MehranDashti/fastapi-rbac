from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_repository import PermissionRepository
from app.tests.factories import make_permission


async def test_get_by_name_found(db_session: AsyncSession):
    await make_permission(db_session, name="users.read")
    result = await PermissionRepository(db_session).get_by_name("users.read")
    assert result is not None
    assert result.name == "users.read"


async def test_get_by_name_not_found(db_session: AsyncSession):
    result = await PermissionRepository(db_session).get_by_name("ghost.read")
    assert result is None


async def test_get_by_name_wrong_guard(db_session: AsyncSession):
    await make_permission(db_session, name="users.read", guard_name="web")
    result = await PermissionRepository(db_session).get_by_name("users.read", guard_name="api")
    assert result is None


async def test_exists_true(db_session: AsyncSession):
    await make_permission(db_session, name="roles.delete")
    assert await PermissionRepository(db_session).exists("roles.delete") is True


async def test_exists_false(db_session: AsyncSession):
    assert await PermissionRepository(db_session).exists("nope.read") is False


async def test_get_all_by_guard_filters_correctly(db_session: AsyncSession):
    await make_permission(db_session, name="a.read", guard_name="api")
    await make_permission(db_session, name="b.read", guard_name="web")
    await make_permission(db_session, name="c.read", guard_name="api")

    repo = PermissionRepository(db_session)
    api_perms = await repo.get_all_by_guard("api")
    web_perms = await repo.get_all_by_guard("web")

    assert len(api_perms) == 2
    assert len(web_perms) == 1
    assert all(p.guard_name == "api" for p in api_perms)
