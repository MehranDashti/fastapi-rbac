import uuid

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_role_permission import Role

_faker = Faker()


def role_payload(**overrides) -> dict:
    return {
        "name": f"role_{uuid.uuid4().hex[:8]}",
        "description": _faker.job(),
        "guard_name": "api",
        **overrides,
    }


async def make_role(
    db: AsyncSession,
    *,
    name: str | None = None,
    description: str | None = None,
    guard_name: str = "api",
) -> Role:
    overrides: dict = {"guard_name": guard_name}
    if name is not None:
        overrides["name"] = name
    if description is not None:
        overrides["description"] = description
    role = Role(**role_payload(**overrides))
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role
