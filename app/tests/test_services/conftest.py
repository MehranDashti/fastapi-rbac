import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.factories import make_permission, make_role, make_user

__all__ = ["make_permission", "make_role", "make_user"]


@pytest.fixture
async def permission(db_session: AsyncSession):
    return await make_permission(db_session)


@pytest.fixture
async def role(db_session: AsyncSession):
    return await make_role(db_session)


@pytest.fixture
async def user(db_session: AsyncSession):
    return await make_user(db_session)
