from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.categories.models import Category
from app.modules.products.models import Product, ProductFAQ, ProductSpec


class ProductRepository:
    async def get_by_id(self, db: AsyncSession, product_id: UUID) -> Optional[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.id == product_id, Product.deleted_at.is_(None))
            .options(
                joinedload(Product.category),
                joinedload(Product.specs),
                joinedload(Product.faqs),
            )
        )
        return result.unique().scalars().first()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.slug == slug, Product.deleted_at.is_(None))
            .options(
                joinedload(Product.category),
                joinedload(Product.specs),
                joinedload(Product.faqs),
            )
        )
        return result.unique().scalars().first()

    async def get_multi(
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
    ) -> list[Product]:
        query = (
            select(Product)
            .where(Product.deleted_at.is_(None))
            .options(joinedload(Product.category))
        )

        if category_slug:
            query = query.join(Category).where(Category.slug == category_slug)

        if price_min is not None:
            query = query.where(Product.price >= price_min)

        if price_max is not None:
            query = query.where(Product.price <= price_max)

        if stock is not None:
            query = query.where(Product.stock == stock)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        if sort_by == "price":
            order_col = Product.price
        elif sort_by == "name":
            order_col = Product.name
        else:
            order_col = Product.created_at

        if sort_order == "desc":
            order_col = order_col.desc()

        query = query.order_by(order_col).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        category_slug: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        stock: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> int:
        query = select(func.count(Product.id)).where(
            Product.deleted_at.is_(None)
        )

        if category_slug:
            query = query.join(Category).where(Category.slug == category_slug)

        if price_min is not None:
            query = query.where(Product.price >= price_min)

        if price_max is not None:
            query = query.where(Product.price <= price_max)

        if stock is not None:
            query = query.where(Product.stock == stock)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar()

    async def create_multi(self, db: AsyncSession, items: list[dict]) -> list[Product]:
        now = datetime.now(timezone.utc)
        products_data = []
        all_specs_data = []
        all_faqs_data = []

        for data in items:
            product_id = uuid4()
            specs = data.pop("specs", None)
            faqs = data.pop("faqs", None)
            all_specs_data.append(specs)
            all_faqs_data.append(faqs)
            products_data.append({
                "id": product_id,
                **data,
                "created_at": now,
                "updated_at": now,
            })

        await db.execute(insert(Product), products_data)

        specs_inserts = [
            {"product_id": p["id"], **s}
            for p, s in zip(products_data, all_specs_data)
            if s
        ]
        if specs_inserts:
            await db.execute(insert(ProductSpec), specs_inserts)

        faqs_inserts = []
        for p, faqs in zip(products_data, all_faqs_data):
            if faqs:
                for faq in faqs:
                    faqs_inserts.append({"product_id": p["id"], **faq})
        if faqs_inserts:
            await db.execute(insert(ProductFAQ), faqs_inserts)

        await db.flush()

        product_ids = [p["id"] for p in products_data]
        result = await db.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .options(
                joinedload(Product.category),
                joinedload(Product.specs),
                joinedload(Product.faqs),
            )
        )
        return result.unique().scalars().all()

    async def create(self, db: AsyncSession, data: dict) -> Product:
        specs_data = data.pop("specs", None)
        faqs_data = data.pop("faqs", None)

        product = Product(**data)
        db.add(product)
        await db.flush()

        if specs_data:
            spec = ProductSpec(product_id=product.id, **specs_data)
            db.add(spec)

        if faqs_data:
            for faq_data in faqs_data:
                faq = ProductFAQ(product_id=product.id, **faq_data)
                db.add(faq)

        await db.flush()
        await db.refresh(product, ["category", "specs", "faqs"])
        return product

    async def update(
        self, db: AsyncSession, product: Product, data: dict
    ) -> Product:
        specs_data = data.pop("specs", None)
        faqs_data = data.pop("faqs", None)

        for field, value in data.items():
            setattr(product, field, value)

        if specs_data is not None:
            if product.specs:
                for field, value in specs_data.items():
                    setattr(product.specs, field, value)
            else:
                spec = ProductSpec(product_id=product.id, **specs_data)
                db.add(spec)

        if faqs_data is not None:
            existing_faqs = await db.execute(
                select(ProductFAQ).where(ProductFAQ.product_id == product.id)
            )
            for faq in existing_faqs.scalars().all():
                await db.delete(faq)

            for faq_data in faqs_data:
                faq = ProductFAQ(product_id=product.id, **faq_data)
                db.add(faq)

        await db.flush()
        await db.refresh(product)
        await db.refresh(product, ["category", "specs", "faqs"])
        return product

    async def soft_delete(self, db: AsyncSession, product: Product) -> Product:
        product.deleted_at = datetime.now(timezone.utc)
        await db.flush()
        return product

    async def hard_delete_all(self, db: AsyncSession) -> None:
        await db.execute(delete(ProductFAQ))
        await db.execute(delete(ProductSpec))
        await db.execute(delete(Product))
        await db.flush()

    async def get_all_export(self, db: AsyncSession) -> list[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.deleted_at.is_(None))
            .options(
                joinedload(Product.specs),
                joinedload(Product.faqs),
            )
            .order_by(Product.created_at)
        )
        return result.unique().scalars().all()

    async def get_newest(self, db: AsyncSession, limit: int) -> list[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.deleted_at.is_(None))
            .options(joinedload(Product.category))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_best_sellers(self, db: AsyncSession, limit: int) -> list[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.deleted_at.is_(None), Product.best_seller.is_(True))
            .options(joinedload(Product.category))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_slugs(self, db: AsyncSession, slugs: list[str]) -> list[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.slug.in_(slugs), Product.deleted_at.is_(None))
            .options(joinedload(Product.category))
        )
        return result.unique().scalars().all()

    async def get_all_slugs(self, db: AsyncSession) -> set[str]:
        result = await db.execute(select(Product.slug))
        return {row[0] for row in result.all()}

    async def get_all_skus(self, db: AsyncSession) -> set[str]:
        result = await db.execute(
            select(Product.sku).where(Product.sku.isnot(None))
        )
        return {row[0] for row in result.all()}

    async def slug_exists(self, db: AsyncSession, slug: str) -> bool:
        result = await db.execute(
            select(Product).where(Product.slug == slug)
        )
        return result.scalars().first() is not None

    async def sku_exists(self, db: AsyncSession, sku: str) -> bool:
        result = await db.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalars().first() is not None


product_repository = ProductRepository()
