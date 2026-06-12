from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_admin_token
from app.modules.testimonials.schemas import (
    TestimonialCreate,
    TestimonialResponse,
)
from app.modules.testimonials.service import testimonial_service

router = APIRouter(prefix="/testimonials", tags=["testimonials"])


@router.get("")
async def list_testimonials(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TestimonialResponse]:
    return await testimonial_service.get_all(db, skip=skip, limit=limit)


@router.get("/{testimonial_id}")
async def get_testimonial(
    testimonial_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TestimonialResponse:
    return await testimonial_service.get_by_id(db, testimonial_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_testimonial(
    data: TestimonialCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TestimonialResponse:
    return await testimonial_service.create(db, data)


@router.delete("/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimonial(
    testimonial_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> None:
    await testimonial_service.delete(db, testimonial_id)
