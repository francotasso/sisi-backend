from typing import Any, Optional
from uuid import UUID

from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.products.models import Product
from app.modules.products.repository import product_repository
from app.modules.products.schemas import (
    BulkErrorDetail,
    ProductBulkRequest,
    ProductBulkResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductExportItem,
    ProductExportResponse,
    ProductListResponse,
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
            ProductListResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                price=p.price,
                discount_price=p.discount_price,
                best_seller=p.best_seller,
                category_id=p.category_id,
                image=p.image,
                short_description=p.short_description,
                stock=p.stock,
                stock_count=p.stock_count,
                sku=p.sku,
                created_at=p.created_at,
                updated_at=p.updated_at,
                category_name=p.category.name if p.category else None,
            )
            for p in products
        ]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_by_slug(
        self, db: AsyncSession, slug: str
    ) -> ProductDetailResponse:
        product = await self.repository.get_by_slug(db, slug)
        if not product:
            raise NotFoundError("Product not found")

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

    async def create(
        self, db: AsyncSession, data: ProductCreate
    ) -> ProductDetailResponse:
        product_data = data.model_dump()
        product_data["slug"] = await self._generate_unique_slug(
            db, product_data["name"]
        )

        product = await self.repository.create(db, product_data)

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

        product = await self.repository.update(db, product, product_data)

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
        products_data = []
        errors = []

        for idx, item in enumerate(data.items):
            try:
                product_dict = item.model_dump()
                product_dict["slug"] = await self._generate_unique_slug(
                    db, product_dict["name"]
                )
                products_data.append(product_dict)
            except Exception as e:
                errors.append(
                    BulkErrorDetail(index=idx, name=item.name, error=str(e))
                )

        if products_data:
            created_products = await self.repository.create_multi(db, products_data)
        else:
            created_products = []

        product_responses = [
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
        ]

        return ProductBulkResponse(
            created=len(product_responses),
            errors=errors,
            products=product_responses,
        )

    async def replace_all(
        self, db: AsyncSession, data: ProductBulkRequest
    ) -> ProductBulkResponse:
        await self.repository.hard_delete_all(db)
        return await self.bulk_create(db, data)

    async def export_all(self, db: AsyncSession) -> ProductExportResponse:
        products = await self.repository.get_all_export(db)
        return ProductExportResponse(
            items=[ProductExportItem.model_validate(p) for p in products]
        )

    async def soft_delete(
        self, db: AsyncSession, product_id: UUID
    ) -> None:
        product = await self.repository.get_by_id(db, product_id)
        if not product:
            raise NotFoundError("Product not found")

        await self.repository.soft_delete(db, product)


product_service = ProductService()
