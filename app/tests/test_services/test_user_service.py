import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    InactiveAccountError,
    NotFoundError,
)
from app.core.permissions import get_all_permissions
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.tests.factories import make_permission, make_role, make_user


def make_service(db: AsyncSession) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )


async def test_register_success(db_session: AsyncSession):
    service = make_service(db_session)
    user = await service.register(
        email="new@test.com",
        username="newuser",
        full_name="New User",
        password="Password1",
    )
    assert user.id is not None
    assert user.email == "new@test.com"


async def test_register_duplicate_email(db_session: AsyncSession):
    await make_user(db_session, email="dup@test.com", username="first")
    service = make_service(db_session)
    with pytest.raises(ConflictError):
        await service.register(
            email="dup@test.com",
            username="second",
            full_name="Second",
            password="Password1",
        )


async def test_register_duplicate_username(db_session: AsyncSession):
    await make_user(db_session, email="first@test.com", username="taken")
    service = make_service(db_session)
    with pytest.raises(ConflictError):
        await service.register(
            email="second@test.com",
            username="taken",
            full_name="Second",
            password="Password1",
        )


async def test_authenticate_success(db_session: AsyncSession):
    await make_user(db_session, email="auth@test.com", username="authuser", password="Password1")
    service = make_service(db_session)
    user = await service.authenticate("auth@test.com", "Password1")
    assert user.email == "auth@test.com"


async def test_authenticate_wrong_password(db_session: AsyncSession):
    await make_user(db_session, email="auth@test.com", username="authuser", password="Password1")
    service = make_service(db_session)
    with pytest.raises(AuthenticationError):
        await service.authenticate("auth@test.com", "WrongPass1")


async def test_authenticate_inactive_user(db_session: AsyncSession):
    await make_user(
        db_session, email="inactive@test.com", username="inactiveuser",
        password="Password1", is_active=False,
    )
    service = make_service(db_session)
    with pytest.raises(InactiveAccountError):
        await service.authenticate("inactive@test.com", "Password1")


async def test_toggle_active(db_session: AsyncSession):
    user = await make_user(db_session, is_active=True)
    service = make_service(db_session)
    toggled = await service.toggle_active(user.id)
    assert toggled.is_active is False
    toggled_back = await service.toggle_active(user.id)
    assert toggled_back.is_active is True


async def test_update_profile_name(db_session: AsyncSession):
    user = await make_user(db_session)
    service = make_service(db_session)
    updated = await service.update_profile(user, full_name="New Name")
    assert updated.full_name == "New Name"


async def test_update_profile_password(db_session: AsyncSession):
    user = await make_user(db_session, email="pw@test.com", username="pwuser", password="OldPass1")
    service = make_service(db_session)
    await service.update_profile(user, password="NewPass1")
    authenticated = await service.authenticate("pw@test.com", "NewPass1")
    assert authenticated.id == user.id


async def test_assign_role_success(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    service = make_service(db_session)
    result = await service.assign_role(user.id, role.id)
    assert any(r.id == role.id for r in result.roles)


async def test_assign_role_already_assigned(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    service = make_service(db_session)
    await service.assign_role(user.id, role.id)
    with pytest.raises(ConflictError):
        await service.assign_role(user.id, role.id)


async def test_assign_role_user_not_found(db_session: AsyncSession):
    role = await make_role(db_session)
    service = make_service(db_session)
    with pytest.raises(NotFoundError):
        await service.assign_role(9999, role.id)


async def test_assign_role_role_not_found(db_session: AsyncSession):
    user = await make_user(db_session)
    service = make_service(db_session)
    with pytest.raises(NotFoundError):
        await service.assign_role(user.id, 9999)


async def test_revoke_role_success(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    service = make_service(db_session)
    await service.assign_role(user.id, role.id)
    result = await service.revoke_role(user.id, role.id)
    assert not any(r.id == role.id for r in result.roles)


async def test_revoke_role_not_assigned(db_session: AsyncSession):
    user = await make_user(db_session)
    role = await make_role(db_session)
    service = make_service(db_session)
    with pytest.raises(ConflictError):
        await service.revoke_role(user.id, role.id)


async def test_sync_roles(db_session: AsyncSession):
    user = await make_user(db_session)
    r1 = await make_role(db_session, name="r1")
    r2 = await make_role(db_session, name="r2")
    service = make_service(db_session)
    await service.assign_role(user.id, r1.id)
    result = await service.sync_roles(user.id, [r2.id])
    role_ids = [r.id for r in result.roles]
    assert r1.id not in role_ids
    assert r2.id in role_ids


async def test_assign_direct_permission_success(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    result = await service.assign_direct_permission(user.id, perm.id)
    assert any(p.id == perm.id for p in result.direct_permissions)


async def test_assign_direct_permission_already_assigned(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    await service.assign_direct_permission(user.id, perm.id)
    with pytest.raises(ConflictError):
        await service.assign_direct_permission(user.id, perm.id)


async def test_revoke_direct_permission_success(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    await service.assign_direct_permission(user.id, perm.id)
    result = await service.revoke_direct_permission(user.id, perm.id)
    assert not any(p.id == perm.id for p in result.direct_permissions)


async def test_revoke_direct_permission_not_assigned(db_session: AsyncSession):
    user = await make_user(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    with pytest.raises(ConflictError):
        await service.revoke_direct_permission(user.id, perm.id)


async def test_sync_direct_permissions(db_session: AsyncSession):
    user = await make_user(db_session)
    p1 = await make_permission(db_session, name="p1.a")
    p2 = await make_permission(db_session, name="p2.b")
    service = make_service(db_session)
    await service.assign_direct_permission(user.id, p1.id)
    result = await service.sync_direct_permissions(user.id, [p2.id])
    perm_ids = [p.id for p in result.direct_permissions]
    assert p1.id not in perm_ids
    assert p2.id in perm_ids


async def test_get_all_permissions_via_role(db_session: AsyncSession):
    perm = await make_permission(db_session, name="orders.read")
    role = await make_role(db_session)
    role.permissions.append(perm)
    await db_session.flush()
    user = await make_user(db_session)
    await user.assign_role(db_session, role)
    user = await UserRepository(db_session).get_with_roles_and_permissions(user.id)

    all_perms = get_all_permissions(user)
    assert "orders.read" in all_perms


async def test_get_all_permissions_direct(db_session: AsyncSession):
    perm = await make_permission(db_session, name="orders.write")
    user = await make_user(db_session)
    await user.give_permission_to(db_session, perm)
    user = await UserRepository(db_session).get_with_roles_and_permissions(user.id)

    all_perms = get_all_permissions(user)
    assert "orders.write" in all_perms


async def test_get_all_permissions_union(db_session: AsyncSession):
    shared = await make_permission(db_session, name="shared.perm")
    direct_only = await make_permission(db_session, name="direct.only")
    role = await make_role(db_session)
    role.permissions.append(shared)
    await db_session.flush()

    user = await make_user(db_session)
    await user.assign_role(db_session, role)
    await user.give_permission_to(db_session, shared)
    await user.give_permission_to(db_session, direct_only)
    user = await UserRepository(db_session).get_with_roles_and_permissions(user.id)

    all_perms = get_all_permissions(user)
    assert all_perms == {"shared.perm", "direct.only"}
