from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, SoftDeleteMixin, TimestampMixin

import uuid


class Product(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "products"

    __table_args__ = (
        Index("ix_products_category_price", "category_id", "price"),
        Index("ix_products_stock_price", "stock", "price"),
        Index("ix_products_active_slug", "slug", postgresql_where=text("deleted_at IS NULL")),
        Index(
            "ix_products_active_category_price",
            "category_id",
            "price",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), index=True, nullable=False
    )
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stock_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    best_seller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    category: Mapped["Category"] = relationship(
        "Category", back_populates="products"
    )
    specs: Mapped[Optional["ProductSpec"]] = relationship(
        "ProductSpec", back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    faqs: Mapped[list["ProductFAQ"]] = relationship(
        "ProductFAQ", back_populates="product", cascade="all, delete-orphan"
    )


class ProductSpec(TimestampMixin, Base):
    __tablename__ = "product_specs"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), unique=True, index=True, nullable=False
    )
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shade: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    finish: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spf: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    skin_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    includes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product", back_populates="specs"
    )


class ProductFAQ(TimestampMixin, Base):
    __tablename__ = "product_faqs"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), index=True, nullable=False
    )
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    product: Mapped["Product"] = relationship(
        "Product", back_populates="faqs"
    )
