import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.services.role_service import RoleService
from app.tests.conftest import make_permission, make_role


def make_service(db: AsyncSession) -> RoleService:
    return RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )


async def test_create_success(db_session: AsyncSession):
    service = make_service(db_session)
    role = await service.create(name="editor", display_name="Editor")
    assert role.id is not None
    assert role.name == "editor"


async def test_create_duplicate(db_session: AsyncSession):
    service = make_service(db_session)
    await service.create(name="editor", display_name="Editor")
    with pytest.raises(HTTPException) as exc:
        await service.create(name="editor", display_name="Editor Again")
    assert exc.value.status_code == 409


async def test_update_success(db_session: AsyncSession):
    role = await make_role(db_session, name="viewer")
    service = make_service(db_session)
    updated = await service.update(role.id, display_name="Viewer Updated")
    assert updated.display_name == "Viewer Updated"


async def test_update_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.update(9999, display_name="X")
    assert exc.value.status_code == 404


async def test_delete_success(db_session: AsyncSession):
    role = await make_role(db_session, name="tobedeleted")
    service = make_service(db_session)
    await service.delete(role.id)
    assert await RoleRepository(db_session).get_by_id(role.id) is None


async def test_delete_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.delete(9999)
    assert exc.value.status_code == 404


async def test_assign_permission_success(db_session: AsyncSession):
    role = await make_role(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    result = await service.assign_permission(role.id, perm.id)
    assert perm in result.permissions


async def test_assign_permission_already_assigned(db_session: AsyncSession):
    role = await make_role(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    await service.assign_permission(role.id, perm.id)
    with pytest.raises(HTTPException) as exc:
        await service.assign_permission(role.id, perm.id)
    assert exc.value.status_code == 409


async def test_revoke_permission_success(db_session: AsyncSession):
    role = await make_role(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    await service.assign_permission(role.id, perm.id)
    result = await service.revoke_permission(role.id, perm.id)
    assert perm not in result.permissions


async def test_revoke_permission_not_assigned(db_session: AsyncSession):
    role = await make_role(db_session)
    perm = await make_permission(db_session, name="posts.read")
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.revoke_permission(role.id, perm.id)
    assert exc.value.status_code == 409


async def test_get_by_name_success(db_session: AsyncSession):
    await make_role(db_session, name="superadmin")
    service = make_service(db_session)
    role = await service.get_by_name("superadmin")
    assert role.name == "superadmin"


async def test_get_by_name_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_name("ghost")
    assert exc.value.status_code == 404
