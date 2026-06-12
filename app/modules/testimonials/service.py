from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.testimonials.repository import testimonial_repository
from app.modules.testimonials.schemas import (
    TestimonialCreate,
    TestimonialResponse,
)


class TestimonialService:
    def __init__(self) -> None:
        self.repository = testimonial_repository

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[TestimonialResponse]:
        testimonials = await self.repository.get_multi(db, skip=skip, limit=limit)
        return [TestimonialResponse.model_validate(t) for t in testimonials]

    async def get_by_id(
        self, db: AsyncSession, testimonial_id: UUID
    ) -> TestimonialResponse:
        testimonial = await self.repository.get_by_id(db, testimonial_id)
        if not testimonial:
            raise NotFoundError("Testimonial not found")
        return TestimonialResponse.model_validate(testimonial)

    async def create(
        self, db: AsyncSession, data: TestimonialCreate
    ) -> TestimonialResponse:
        testimonial_data = data.model_dump()
        testimonial = await self.repository.create(db, testimonial_data)
        return TestimonialResponse.model_validate(testimonial)

    async def delete(self, db: AsyncSession, testimonial_id: UUID) -> None:
        testimonial = await self.repository.get_by_id(db, testimonial_id)
        if not testimonial:
            raise NotFoundError("Testimonial not found")
        await self.repository.delete(db, testimonial)


testimonial_service = TestimonialService()
