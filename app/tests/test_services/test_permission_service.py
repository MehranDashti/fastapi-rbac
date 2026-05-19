import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_repository import PermissionRepository
from app.services.permission_service import PermissionService
from app.tests.conftest import make_permission


def make_service(db: AsyncSession) -> PermissionService:
    return PermissionService(repo=PermissionRepository(db))


async def test_create_success(db_session: AsyncSession):
    service = make_service(db_session)
    perm = await service.create(name="posts.read", display_name="Read Posts")
    assert perm.id is not None
    assert perm.name == "posts.read"


async def test_create_duplicate(db_session: AsyncSession):
    service = make_service(db_session)
    await service.create(name="posts.read", display_name="Read Posts")
    with pytest.raises(HTTPException) as exc:
        await service.create(name="posts.read", display_name="Read Posts Again")
    assert exc.value.status_code == 409


async def test_update_success(db_session: AsyncSession):
    perm = await make_permission(db_session, name="posts.write")
    service = make_service(db_session)
    updated = await service.update(perm.id, display_name="Write Posts Updated")
    assert updated.display_name == "Write Posts Updated"


async def test_update_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.update(9999, display_name="X")
    assert exc.value.status_code == 404


async def test_delete_success(db_session: AsyncSession):
    perm = await make_permission(db_session, name="posts.delete")
    service = make_service(db_session)
    await service.delete(perm.id)
    assert await PermissionRepository(db_session).get_by_id(perm.id) is None


async def test_delete_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.delete(9999)
    assert exc.value.status_code == 404


async def test_get_all_by_guard(db_session: AsyncSession):
    await make_permission(db_session, name="a.read", guard_name="api")
    await make_permission(db_session, name="b.read", guard_name="web")
    service = make_service(db_session)
    api_perms = await service.get_all("api")
    web_perms = await service.get_all("web")
    assert len(api_perms) == 1
    assert len(web_perms) == 1


async def test_get_by_name_success(db_session: AsyncSession):
    await make_permission(db_session, name="users.read")
    service = make_service(db_session)
    perm = await service.get_by_name("users.read")
    assert perm.name == "users.read"


async def test_get_by_name_not_found(db_session: AsyncSession):
    service = make_service(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_name("ghost.read")
    assert exc.value.status_code == 404
