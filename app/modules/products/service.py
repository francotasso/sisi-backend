import hashlib
import json
import secrets
import string
from uuid import uuid4
from typing import Any, Optional
from uuid import UUID

from fastapi import UploadFile
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.exceptions import NotFoundError
from app.core.storage import cloudinary_service
from app.modules.products.models import Product
from app.modules.products.repository import product_repository
from app.modules.products.schemas import (
    BulkErrorDetail,
    ProductBulkRequest,
    ProductBulkResponse,
    ProductCardResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductExportItem,
    ProductExportResponse,
    ProductUpdate,
)


class ProductService:
    def __init__(self) -> None:
        self.repository = product_repository

    async def _generate_unique_slug(
        self, db: AsyncSession, name: str
    ) -> str:
        base = slugify(name)
        slug = base
        counter = 1
        while await self.repository.slug_exists(db, slug):
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    async def _generate_sku(self, db: AsyncSession) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            sku = "SIS-" + "".join(secrets.choice(alphabet) for _ in range(8))
            if not await self.repository.sku_exists(db, sku):
                return sku

    async def get_list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        category_slug: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        stock: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> dict[str, Any]:
        params = {
            "skip": skip,
            "limit": limit,
            "category_slug": category_slug,
            "price_min": price_min,
            "price_max": price_max,
            "stock": stock,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        cache_key = (
            "sisi:products:list:"
            + hashlib.sha256(
                json.dumps(params, sort_keys=True, default=str).encode()
            ).hexdigest()
        )

        cached = await cache_get(cache_key)
        if cached is not None:
            return {
                "items": [ProductCardResponse(**item) for item in cached["items"]],
                "total": cached["total"],
                "skip": cached["skip"],
                "limit": cached["limit"],
            }

        products = await self.repository.get_multi(
            db,
            skip=skip,
            limit=limit,
            category_slug=category_slug,
            price_min=price_min,
            price_max=price_max,
            stock=stock,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await self.repository.count(
            db,
            category_slug=category_slug,
            price_min=price_min,
            price_max=price_max,
            stock=stock,
            search=search,
        )

        items = [
            ProductCardResponse(
                name=p.name,
                slug=p.slug,
                price=p.price,
                discount_price=p.discount_price,
                image=p.image,
                stock=p.stock,
                sku=p.sku,
                category_name=p.category.name if p.category else None,
                created_at=p.created_at,
            )
            for p in products
        ]

        await cache_set(cache_key, 120, {
            "items": [i.model_dump(mode="json") for i in items],
            "total": total,
            "skip": skip,
            "limit": limit,
        })

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_by_slug(
        self, db: AsyncSession, slug: str
    ) -> ProductDetailResponse:
        cache_key = f"sisi:products:slug:{slug}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return ProductDetailResponse(**cached)

        product = await self.repository.get_by_slug(db, slug)
        if not product:
            raise NotFoundError("Product not found")

        result = ProductDetailResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            price=product.price,
            category_id=product.category_id,
            image=product.image,
            description=product.description,
            short_description=product.short_description,
            stock=product.stock,
            stock_count=product.stock_count,
            sku=product.sku,
            discount_price=product.discount_price,
            best_seller=product.best_seller,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=product.category.name if product.category else None,
            specs=product.specs,
            faqs=product.faqs,
        )
        await cache_set(cache_key, 300, result.model_dump(mode="json"))
        return result

    async def create(
        self, db: AsyncSession, data: ProductCreate
    ) -> ProductDetailResponse:
        product_data = data.model_dump()
        product_data["slug"] = await self._generate_unique_slug(
            db, product_data["name"]
        )

        if not product_data.get("sku"):
            product_data["sku"] = await self._generate_sku(db)

        product = await self.repository.create(db, product_data)
        await cache_delete("sisi:products:*")

        return ProductDetailResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            price=product.price,
            category_id=product.category_id,
            image=product.image,
            description=product.description,
            short_description=product.short_description,
            stock=product.stock,
            stock_count=product.stock_count,
            sku=product.sku,
            discount_price=product.discount_price,
            best_seller=product.best_seller,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=product.category.name if product.category else None,
            specs=product.specs,
            faqs=product.faqs,
        )

    async def update(
        self, db: AsyncSession, product_id: UUID, data: ProductUpdate
    ) -> ProductDetailResponse:
        product = await self.repository.get_by_id(db, product_id)
        if not product:
            raise NotFoundError("Product not found")

        product_data = data.model_dump(exclude_unset=True)

        if "name" in product_data and product_data["name"] != product.name:
            product_data["slug"] = await self._generate_unique_slug(
                db, product_data["name"]
            )

        if "image" in product_data and product.image:
            cloudinary_service.delete(product.image)

        product = await self.repository.update(db, product, product_data)
        await cache_delete("sisi:products:*")

        return ProductDetailResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            price=product.price,
            category_id=product.category_id,
            image=product.image,
            description=product.description,
            short_description=product.short_description,
            stock=product.stock,
            stock_count=product.stock_count,
            sku=product.sku,
            discount_price=product.discount_price,
            best_seller=product.best_seller,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=product.category.name if product.category else None,
            specs=product.specs,
            faqs=product.faqs,
        )

    async def bulk_create(
        self, db: AsyncSession, data: ProductBulkRequest
    ) -> ProductBulkResponse:
        existing_slugs = await self.repository.get_all_slugs(db)
        existing_skus = await self.repository.get_all_skus(db)

        batch_slugs: set[str] = set(existing_slugs)
        batch_skus: set[str] = set(existing_skus)

        alphabet = string.ascii_uppercase + string.digits
        products_data: list[dict] = []
        errors: list[BulkErrorDetail] = []

        for idx, item in enumerate(data.items):
            try:
                product_dict = item.model_dump()

                base = slugify(product_dict["name"])
                slug = base
                counter = 1
                while slug in batch_slugs:
                    slug = f"{base}-{counter}"
                    counter += 1
                product_dict["slug"] = slug
                batch_slugs.add(slug)

                if not product_dict.get("sku"):
                    while True:
                        sku = "SIS-" + "".join(
                            secrets.choice(alphabet) for _ in range(8)
                        )
                        if sku not in batch_skus:
                            break
                    product_dict["sku"] = sku
                    batch_skus.add(sku)

                products_data.append(product_dict)
            except Exception as e:
                errors.append(
                    BulkErrorDetail(index=idx, name=item.name, error=str(e))
                )

        if products_data:
            created_products = await self.repository.create_multi(db, products_data)
        else:
            created_products = []

        await cache_delete("sisi:products:*")

        return ProductBulkResponse(
            created=len(created_products),
            errors=errors,
            products=[
                ProductDetailResponse(
                    id=p.id,
                    name=p.name,
                    slug=p.slug,
                    price=p.price,
                    discount_price=p.discount_price,
                    best_seller=p.best_seller,
                    category_id=p.category_id,
                    image=p.image,
                    description=p.description,
                    short_description=p.short_description,
                    stock=p.stock,
                    stock_count=p.stock_count,
                    sku=p.sku,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    category_name=p.category.name if p.category else None,
                    specs=p.specs,
                    faqs=p.faqs,
                )
                for p in created_products
            ],
        )

    async def replace_all(
        self, db: AsyncSession, data: ProductBulkRequest
    ) -> ProductBulkResponse:
        await self.repository.hard_delete_all(db)
        return await self.bulk_create(db, data)

    async def get_newest(
        self, db: AsyncSession, limit: int
    ) -> list[ProductCardResponse]:
        cache_key = f"sisi:products:newest:{limit}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return [ProductCardResponse(**item) for item in cached]

        products = await self.repository.get_newest(db, limit)
        result = [
            ProductCardResponse(
                name=p.name,
                slug=p.slug,
                price=p.price,
                discount_price=p.discount_price,
                image=p.image,
                stock=p.stock,
                sku=p.sku,
                category_name=p.category.name if p.category else None,
                created_at=p.created_at,
            )
            for p in products
        ]
        await cache_set(
            cache_key, 300, [r.model_dump(mode="json") for r in result]
        )
        return result

    async def get_best_sellers(
        self, db: AsyncSession, limit: int
    ) -> list[ProductCardResponse]:
        cache_key = f"sisi:products:best-sellers:{limit}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return [ProductCardResponse(**item) for item in cached]

        products = await self.repository.get_best_sellers(db, limit)
        result = [
            ProductCardResponse(
                name=p.name,
                slug=p.slug,
                price=p.price,
                discount_price=p.discount_price,
                image=p.image,
                stock=p.stock,
                sku=p.sku,
                category_name=p.category.name if p.category else None,
                created_at=p.created_at,
            )
            for p in products
        ]
        await cache_set(
            cache_key, 300, [r.model_dump(mode="json") for r in result]
        )
        return result

    async def get_by_slugs(
        self, db: AsyncSession, slugs: list[str]
    ) -> list[ProductCardResponse]:
        products = await self.repository.get_by_slugs(db, slugs)
        return [
            ProductCardResponse(
                name=p.name,
                slug=p.slug,
                price=p.price,
                discount_price=p.discount_price,
                stock=p.stock,
                sku=p.sku,
                image=p.image,
                category_name=p.category.name if p.category else None,
                created_at=p.created_at,
            )
            for p in products
        ]

    async def export_all(self, db: AsyncSession) -> ProductExportResponse:
        products = await self.repository.get_all_export(db)
        return ProductExportResponse(
            items=[ProductExportItem.model_validate(p) for p in products]
        )

    async def upload_image(
        self, db: AsyncSession, product_id: UUID, file: UploadFile
    ) -> ProductDetailResponse:
        product = await self.repository.get_by_id(db, product_id)
        if not product:
            raise NotFoundError("Product not found")

        if product.image:
            cloudinary_service.delete(product.image)

        url = await cloudinary_service.upload(file)

        product.image = url
        await db.flush()
        await db.refresh(product)
        await db.refresh(product, ["category", "specs", "faqs"])
        await cache_delete("sisi:products:*")
        return ProductDetailResponse(

            id=product.id,
            name=product.name,
            slug=product.slug,
            price=product.price,
            category_id=product.category_id,
            image=product.image,
            description=product.description,
            short_description=product.short_description,
            stock=product.stock,
            stock_count=product.stock_count,
            sku=product.sku,
            discount_price=product.discount_price,
            best_seller=product.best_seller,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=product.category.name if product.category else None,
            specs=product.specs,
            faqs=product.faqs,
        )

    async def soft_delete(
        self, db: AsyncSession, product_id: UUID
    ) -> None:
        product = await self.repository.get_by_id(db, product_id)
        if not product:
            raise NotFoundError("Product not found")

        await self.repository.soft_delete(db, product)
        await cache_delete("sisi:products:*")


product_service = ProductService()
