from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )
