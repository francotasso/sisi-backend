from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.exceptions import DuplicateError, NotFoundError
from app.core.storage import cloudinary_service
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
        cached = await cache_get("sisi:categories")
        if cached is not None:
            return [CategoryResponse.model_validate(item) for item in cached]
        categories = await self.repository.get_multi(db)
        result = [CategoryResponse.model_validate(c) for c in categories]
        await cache_set(
            "sisi:categories", 3600, [r.model_dump(mode="json") for r in result]
        )
        return result

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

        category_data = {
            "name": data.name,
            "slug": slug,
            "short_description": data.short_description,
            "image": data.image,
        }
        category = await self.repository.create(db, category_data)
        await cache_delete("sisi:categories")
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

        if "image" in category_data and category.image:
            cloudinary_service.delete(category.image)

        category = await self.repository.update(db, category, category_data)
        await cache_delete("sisi:categories")
        return CategoryResponse.model_validate(category)

    async def upload_image(
        self, db: AsyncSession, category_id: UUID, file: UploadFile
    ) -> CategoryResponse:
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category not found")

        if category.image:
            cloudinary_service.delete(category.image)

        url = await cloudinary_service.upload(file, folder="categories")
        category.image = url
        await db.flush()
        await db.refresh(category)

        await cache_delete("sisi:categories")
        return CategoryResponse.model_validate(category)

    async def delete(self, db: AsyncSession, category_id: UUID) -> None:
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category not found")
        await self.repository.delete(db, category)
        await cache_delete("sisi:categories")


category_service = CategoryService()
