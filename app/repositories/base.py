from typing import Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> T | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_all(self) -> list[T]:
        result = await self.db.execute(select(self.model))
        return list(result.scalars().all())

    async def create(self, instance: T) -> T:
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: T) -> None:
        await self.db.delete(instance)
        await self.db.flush()