from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.role_repository import RoleRepository
from app.tests.factories import make_permission, make_role


async def test_get_by_name_found(db_session: AsyncSession):
    await make_role(db_session, name="admin")
    result = await RoleRepository(db_session).get_by_name("admin")
    assert result is not None
    assert result.name == "admin"


async def test_get_by_name_not_found(db_session: AsyncSession):
    assert await RoleRepository(db_session).get_by_name("ghost") is None


async def test_get_by_name_wrong_guard(db_session: AsyncSession):
    await make_role(db_session, name="editor", guard_name="web")
    assert await RoleRepository(db_session).get_by_name("editor", guard_name="api") is None


async def test_exists_true(db_session: AsyncSession):
    await make_role(db_session, name="moderator")
    assert await RoleRepository(db_session).exists("moderator") is True


async def test_exists_false(db_session: AsyncSession):
    assert await RoleRepository(db_session).exists("phantom") is False


async def test_get_with_permissions_loaded(db_session: AsyncSession):
    perm = await make_permission(db_session, name="posts.read")
    role = await make_role(db_session, name="editor")
    role.permissions.append(perm)
    await db_session.flush()

    loaded = await RoleRepository(db_session).get_with_permissions(role.id)
    assert loaded is not None
    assert len(loaded.permissions) == 1
    assert loaded.permissions[0].name == "posts.read"


async def test_assign_permission_idempotent(db_session: AsyncSession):
    perm = await make_permission(db_session)
    role = await make_role(db_session)
    repo = RoleRepository(db_session)

    await repo.assign_permission(role, perm)
    await repo.assign_permission(role, perm)
    assert len(role.permissions) == 1


async def test_revoke_permission_idempotent(db_session: AsyncSession):
    perm = await make_permission(db_session)
    role = await make_role(db_session)
    repo = RoleRepository(db_session)

    await repo.revoke_permission(role, perm)  # not assigned — no error
    assert len(role.permissions) == 0


async def test_assign_then_revoke_permission(db_session: AsyncSession):
    perm = await make_permission(db_session)
    role = await make_role(db_session)
    repo = RoleRepository(db_session)

    await repo.assign_permission(role, perm)
    assert len(role.permissions) == 1

    await repo.revoke_permission(role, perm)
    assert len(role.permissions) == 0
