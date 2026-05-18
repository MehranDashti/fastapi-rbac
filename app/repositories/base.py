from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository with common CRUD operations.
    Extend this for every model — no boilerplate repetition.
    """

    model: Type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelT]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ModelT]:
        result = await self.db.execute(select(self.model))
        return result.scalars().all()

    async def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        await self.db.flush()  # get PK without committing (session commit happens in get_db)
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.db.delete(obj)
        await self.db.flush()