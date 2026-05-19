from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.tests.conftest import make_permission, make_role, make_user


async def test_get_by_email_found(db_session: AsyncSession):
    user = await make_user(db_session, email="a@test.com", username="usera")
    result = await UserRepository(db_session).get_by_email("a@test.com")
    assert result is not None
    assert result.id == user.id


async def test_get_by_email_not_found(db_session: AsyncSession):
    assert await UserRepository(db_session).get_by_email("missing@test.com") is None


async def test_get_by_username_found(db_session: AsyncSession):
    await make_user(db_session, username="findme", email="b@test.com")
    result = await UserRepository(db_session).get_by_username("findme")
    assert result is not None
    assert result.username == "findme"


async def test_get_by_username_not_found(db_session: AsyncSession):
    assert await UserRepository(db_session).get_by_username("ghost") is None


async def test_email_exists_true(db_session: AsyncSession):
    await make_user(db_session, email="exists@test.com", username="exists")
    assert await UserRepository(db_session).email_exists("exists@test.com") is True


async def test_email_exists_false(db_session: AsyncSession):
    assert await UserRepository(db_session).email_exists("no@test.com") is False


async def test_username_exists_true(db_session: AsyncSession):
    await make_user(db_session, username="taken", email="c@test.com")
    assert await UserRepository(db_session).username_exists("taken") is True


async def test_username_exists_false(db_session: AsyncSession):
    assert await UserRepository(db_session).username_exists("free") is False


async def test_get_with_roles_and_permissions(db_session: AsyncSession):
    perm = await make_permission(db_session, name="x.read")
    role = await make_role(db_session)
    role.permissions.append(perm)
    await db_session.flush()

    user = await make_user(db_session)
    user.roles.append(role)
    await db_session.flush()

    loaded = await UserRepository(db_session).get_with_roles_and_permissions(user.id)
    assert loaded is not None
    assert len(loaded.roles) == 1
    assert len(loaded.roles[0].permissions) == 1
    assert loaded.roles[0].permissions[0].name == "x.read"


async def test_get_with_roles_and_direct_permissions(db_session: AsyncSession):
    perm = await make_permission(db_session, name="y.write")
    user = await make_user(db_session)
    user.direct_permissions.append(perm)
    await db_session.flush()

    loaded = await UserRepository(db_session).get_with_roles_and_permissions(user.id)
    assert loaded is not None
    assert len(loaded.direct_permissions) == 1
    assert loaded.direct_permissions[0].name == "y.write"


async def test_assign_role_idempotent(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    repo = UserRepository(db_session)

    await repo.assign_role(user, role)
    await repo.assign_role(user, role)
    assert len(user.roles) == 1


async def test_revoke_role_idempotent(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    repo = UserRepository(db_session)

    await repo.revoke_role(user, role)  # not assigned — no error
    assert len(user.roles) == 0


async def test_sync_roles_replaces(db_session: AsyncSession):
    user = await make_user(db_session)
    r1 = await make_role(db_session, name="r1")
    r2 = await make_role(db_session, name="r2")
    repo = UserRepository(db_session)

    await repo.assign_role(user, r1)
    await repo.sync_roles(user, [r2])

    assert len(user.roles) == 1
    assert user.roles[0].name == "r2"


async def test_assign_direct_permission_idempotent(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session)
    repo = UserRepository(db_session)

    await repo.assign_direct_permission(user, perm)
    await repo.assign_direct_permission(user, perm)
    assert len(user.direct_permissions) == 1


async def test_revoke_direct_permission_idempotent(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session)
    repo = UserRepository(db_session)

    await repo.revoke_direct_permission(user, perm)  # not assigned — no error
    assert len(user.direct_permissions) == 0


async def test_sync_direct_permissions_replaces(db_session: AsyncSession):
    user = await make_user(db_session)
    p1 = await make_permission(db_session, name="p1.a")
    p2 = await make_permission(db_session, name="p2.b")
    repo = UserRepository(db_session)

    await repo.assign_direct_permission(user, p1)
    await repo.sync_direct_permissions(user, [p2])

    assert len(user.direct_permissions) == 1
    assert user.direct_permissions[0].name == "p2.b"
