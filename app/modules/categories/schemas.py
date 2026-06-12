from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
