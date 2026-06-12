from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TestimonialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    avatar: Optional[str] = None


class TestimonialResponse(BaseModel):
    id: UUID
    name: str
    text: str
    rating: int
    avatar: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
