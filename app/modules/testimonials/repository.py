from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.testimonials.models import Testimonial


class TestimonialRepository:
    async def get_by_id(
        self, db: AsyncSession, testimonial_id: UUID
    ) -> Optional[Testimonial]:
        result = await db.execute(
            select(Testimonial).where(Testimonial.id == testimonial_id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[Testimonial]:
        result = await db.execute(
            select(Testimonial)
            .order_by(Testimonial.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, data: dict) -> Testimonial:
        testimonial = Testimonial(**data)
        db.add(testimonial)
        await db.flush()
        await db.refresh(testimonial)
        return testimonial

    async def delete(
        self, db: AsyncSession, testimonial: Testimonial
    ) -> None:
        await db.delete(testimonial)
        await db.flush()


testimonial_repository = TestimonialRepository()
