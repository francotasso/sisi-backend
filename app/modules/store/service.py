from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.store.repository import store_repository
from app.modules.store.schemas import StoreCreate, StoreResponse, StoreUpdate


class StoreService:
    def __init__(self) -> None:
        self.repository = store_repository

    async def get(self, db: AsyncSession) -> StoreResponse:
        store = await self.repository.get(db)
        if not store:
            raise NotFoundError("Store not found. Please create one first.")
        return StoreResponse.model_validate(store)

    async def create(
        self, db: AsyncSession, data: StoreCreate
    ) -> StoreResponse:
        existing = await self.repository.get(db)
        if existing:
            raise NotFoundError("Store already exists. Use PUT to update.")

        store_data = data.model_dump()
        store = await self.repository.create(db, store_data)
        return StoreResponse.model_validate(store)

    async def update(
        self, db: AsyncSession, data: StoreUpdate
    ) -> StoreResponse:
        store = await self.repository.get(db)
        if not store:
            raise NotFoundError("Store not found. Use POST to create one first.")

        store_data = data.model_dump(exclude_unset=True)
        store = await self.repository.update(db, store, store_data)
        return StoreResponse.model_validate(store)


store_service = StoreService()
