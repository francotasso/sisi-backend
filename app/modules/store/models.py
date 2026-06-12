from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

import uuid


class Store(TimestampMixin, Base):
    __tablename__ = "stores"

    store_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contact: Mapped[Optional["StoreContact"]] = relationship(
        "StoreContact", back_populates="store", uselist=False, cascade="all, delete-orphan"
    )
    hours: Mapped[list["StoreHour"]] = relationship(
        "StoreHour", back_populates="store", cascade="all, delete-orphan"
    )
    social_media: Mapped[list["StoreSocialMedia"]] = relationship(
        "StoreSocialMedia", back_populates="store", cascade="all, delete-orphan"
    )


class StoreContact(TimestampMixin, Base):
    __tablename__ = "store_contacts"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), unique=True, index=True, nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_map: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    store: Mapped["Store"] = relationship("Store", back_populates="contact")


class StoreHour(TimestampMixin, Base):
    __tablename__ = "store_hours"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), index=True, nullable=False
    )
    day: Mapped[str] = mapped_column(String(20), nullable=False)
    open_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    close_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_closed: Mapped[bool] = mapped_column(default=False, nullable=False)

    store: Mapped["Store"] = relationship("Store", back_populates="hours")


class StoreSocialMedia(TimestampMixin, Base):
    __tablename__ = "store_social_media"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), index=True, nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    store: Mapped["Store"] = relationship("Store", back_populates="social_media")
