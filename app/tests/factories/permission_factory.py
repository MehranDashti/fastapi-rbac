import uuid

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_role_permission import Permission

_faker = Faker()


def permission_payload(**overrides) -> dict:
    return {
        "name": f"{_faker.word()}.{_faker.word()}_{uuid.uuid4().hex[:6]}",
        "description": _faker.sentence(nb_words=3).rstrip("."),
        "guard_name": "api",
        **overrides,
    }


async def make_permission(
    db: AsyncSession,
    *,
    name: str | None = None,
    description: str | None = None,
    guard_name: str = "api",
) -> Permission:
    overrides: dict = {"guard_name": guard_name}
    if name is not None:
        overrides["name"] = name
    if description is not None:
        overrides["description"] = description
    perm = Permission(**permission_payload(**overrides))
    db.add(perm)
    await db.flush()
    await db.refresh(perm)
    return perm
