from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    image: Optional[str] = Field(None, max_length=500)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    image: Optional[str] = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    short_description: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
