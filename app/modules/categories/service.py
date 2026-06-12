from typing import Optional
from uuid import UUID

from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError
from app.modules.categories.repository import category_repository
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


class CategoryService:
    def __init__(self) -> None:
        self.repository = category_repository

    async def get_all(self, db: AsyncSession) -> list[CategoryResponse]:
        categories = await self.repository.get_multi(db)
        return [CategoryResponse.model_validate(c) for c in categories]

    async def get_by_id(
        self, db: AsyncSession, category_id: UUID
    ) -> CategoryResponse:
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category not found")
        return CategoryResponse.model_validate(category)

    async def get_by_slug(
        self, db: AsyncSession, slug: str
    ) -> CategoryResponse:
        category = await self.repository.get_by_slug(db, slug)
        if not category:
            raise NotFoundError("Category not found")
        return CategoryResponse.model_validate(category)

    async def create(
        self, db: AsyncSession, data: CategoryCreate
    ) -> CategoryResponse:
        slug = slugify(data.name)

        existing = await self.repository.get_by_slug(db, slug)
        if existing:
            raise DuplicateError("Category with this name already exists")

        category_data = {"name": data.name, "slug": slug}
        category = await self.repository.create(db, category_data)
        return CategoryResponse.model_validate(category)

    async def update(
        self, db: AsyncSession, category_id: UUID, data: CategoryUpdate
    ) -> CategoryResponse:
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category not found")

        category_data = data.model_dump(exclude_unset=True)

        if "name" in category_data and category_data["name"] != category.name:
            slug = slugify(category_data["name"])
            existing = await self.repository.get_by_slug(db, slug)
            if existing and existing.id != category_id:
                raise DuplicateError("Category with this name already exists")
            category_data["slug"] = slug

        category = await self.repository.update(db, category, category_data)
        return CategoryResponse.model_validate(category)

    async def delete(self, db: AsyncSession, category_id: UUID) -> None:
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category not found")
        await self.repository.delete(db, category)


category_service = CategoryService()
