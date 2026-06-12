from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.store.models import (
    Store,
    StoreContact,
    StoreHour,
    StoreSocialMedia,
)


class StoreRepository:
    async def get(self, db: AsyncSession) -> Optional[Store]:
        result = await db.execute(
            select(Store)
            .options(
                joinedload(Store.contact),
                joinedload(Store.hours),
                joinedload(Store.social_media),
            )
            .limit(1)
        )
        return result.unique().scalars().first()

    async def get_by_id(self, db: AsyncSession, store_id: UUID) -> Optional[Store]:
        result = await db.execute(
            select(Store)
            .where(Store.id == store_id)
            .options(
                joinedload(Store.contact),
                joinedload(Store.hours),
                joinedload(Store.social_media),
            )
        )
        return result.unique().scalars().first()

    async def create(self, db: AsyncSession, data: dict) -> Store:
        contact_data = data.pop("contact", None)
        hours_data = data.pop("hours", None)
        social_data = data.pop("social_media", None)

        store = Store(**data)
        db.add(store)
        await db.flush()

        if contact_data:
            contact = StoreContact(store_id=store.id, **contact_data)
            db.add(contact)

        if hours_data:
            for hour_data in hours_data:
                hour = StoreHour(store_id=store.id, **hour_data)
                db.add(hour)

        if social_data:
            for soc_data in social_data:
                soc = StoreSocialMedia(store_id=store.id, **soc_data)
                db.add(soc)

        await db.flush()
        await db.refresh(store)
        await db.refresh(store, ["contact", "hours", "social_media"])
        return store

    async def update(
        self, db: AsyncSession, store: Store, data: dict
    ) -> Store:
        contact_data = data.pop("contact", None)
        hours_data = data.pop("hours", None)
        social_data = data.pop("social_media", None)

        for field, value in data.items():
            setattr(store, field, value)

        if contact_data is not None:
            if store.contact:
                for field, value in contact_data.items():
                    setattr(store.contact, field, value)
            else:
                contact = StoreContact(store_id=store.id, **contact_data)
                db.add(contact)

        if hours_data is not None:
            existing_hours = await db.execute(
                select(StoreHour).where(StoreHour.store_id == store.id)
            )
            for h in existing_hours.scalars().all():
                await db.delete(h)

            for hour_data in hours_data:
                hour = StoreHour(store_id=store.id, **hour_data)
                db.add(hour)

        if social_data is not None:
            existing_social = await db.execute(
                select(StoreSocialMedia).where(StoreSocialMedia.store_id == store.id)
            )
            for s in existing_social.scalars().all():
                await db.delete(s)

            for soc_data in social_data:
                soc = StoreSocialMedia(store_id=store.id, **soc_data)
                db.add(soc)

        await db.flush()
        await db.refresh(store)
        await db.refresh(store, ["contact", "hours", "social_media"])
        return store


store_repository = StoreRepository()
