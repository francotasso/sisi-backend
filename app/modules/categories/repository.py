from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category


class CategoryRepository:
    async def get_by_id(self, db: AsyncSession, category_id: UUID) -> Optional[Category]:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalars().first()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Category]:
        result = await db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession) -> list[Category]:
        result = await db.execute(
            select(Category).order_by(Category.name)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, data: dict) -> Category:
        category = Category(**data)
        db.add(category)
        await db.flush()
        await db.refresh(category)
        return category

    async def update(
        self, db: AsyncSession, category: Category, data: dict
    ) -> Category:
        for field, value in data.items():
            setattr(category, field, value)
        await db.flush()
        await db.refresh(category)
        return category

    async def delete(self, db: AsyncSession, category: Category) -> None:
        await db.delete(category)
        await db.flush()


category_repository = CategoryRepository()
