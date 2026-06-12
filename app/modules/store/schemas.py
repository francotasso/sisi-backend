from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StoreContactCreate(BaseModel):
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    address_map: Optional[str] = None


class StoreContactUpdate(BaseModel):
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    address_map: Optional[str] = None


class StoreContactResponse(BaseModel):
    id: UUID
    store_id: UUID
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    address_map: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StoreHourCreate(BaseModel):
    day: str = Field(..., min_length=1, max_length=20)
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    is_closed: bool = False


class StoreHourUpdate(BaseModel):
    day: Optional[str] = Field(None, min_length=1, max_length=20)
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    is_closed: Optional[bool] = None


class StoreHourResponse(BaseModel):
    id: UUID
    store_id: UUID
    day: str
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    is_closed: bool

    model_config = ConfigDict(from_attributes=True)


class StoreSocialMediaCreate(BaseModel):
    platform: str = Field(..., min_length=1, max_length=50)
    url: str = Field(..., min_length=1, max_length=500)


class StoreSocialMediaUpdate(BaseModel):
    platform: Optional[str] = Field(None, min_length=1, max_length=50)
    url: Optional[str] = Field(None, min_length=1, max_length=500)


class StoreSocialMediaResponse(BaseModel):
    id: UUID
    store_id: UUID
    platform: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class StoreCreate(BaseModel):
    store_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contact: Optional[StoreContactCreate] = None
    hours: Optional[list[StoreHourCreate]] = None
    social_media: Optional[list[StoreSocialMediaCreate]] = None


class StoreUpdate(BaseModel):
    store_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    contact: Optional[StoreContactUpdate] = None
    hours: Optional[list[StoreHourUpdate]] = None
    social_media: Optional[list[StoreSocialMediaUpdate]] = None


class StoreResponse(BaseModel):
    id: UUID
    store_name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    contact: Optional[StoreContactResponse] = None
    hours: Optional[list[StoreHourResponse]] = None
    social_media: Optional[list[StoreSocialMediaResponse]] = None

    model_config = ConfigDict(from_attributes=True)
