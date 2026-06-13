from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductSpecCreate(BaseModel):
    brand: Optional[str] = None
    product_type: Optional[str] = None
    shade: Optional[str] = None
    finish: Optional[str] = None
    size: Optional[str] = None
    ingredients: Optional[str] = None
    spf: Optional[str] = None
    skin_type: Optional[str] = None
    notes: Optional[str] = None
    benefits: Optional[str] = None
    includes: Optional[str] = None


class ProductSpecUpdate(BaseModel):
    brand: Optional[str] = None
    product_type: Optional[str] = None
    shade: Optional[str] = None
    finish: Optional[str] = None
    size: Optional[str] = None
    ingredients: Optional[str] = None
    spf: Optional[str] = None
    skin_type: Optional[str] = None
    notes: Optional[str] = None
    benefits: Optional[str] = None
    includes: Optional[str] = None


class ProductSpecResponse(BaseModel):
    id: UUID
    product_id: UUID
    brand: Optional[str] = None
    product_type: Optional[str] = None
    shade: Optional[str] = None
    finish: Optional[str] = None
    size: Optional[str] = None
    ingredients: Optional[str] = None
    spf: Optional[str] = None
    skin_type: Optional[str] = None
    notes: Optional[str] = None
    benefits: Optional[str] = None
    includes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductFAQCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1)


class ProductFAQUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1)


class ProductFAQResponse(BaseModel):
    id: UUID
    product_id: UUID
    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)


class ProductExportSpecResponse(BaseModel):
    brand: Optional[str] = None
    product_type: Optional[str] = None
    shade: Optional[str] = None
    finish: Optional[str] = None
    size: Optional[str] = None
    ingredients: Optional[str] = None
    spf: Optional[str] = None
    skin_type: Optional[str] = None
    notes: Optional[str] = None
    benefits: Optional[str] = None
    includes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductExportFAQResponse(BaseModel):
    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)


class ProductExportItem(BaseModel):
    name: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    image: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    stock: bool
    best_seller: bool = False
    sku: Optional[str] = None
    stock_count: int
    category_id: UUID
    specs: Optional[ProductExportSpecResponse] = None
    faqs: Optional[list[ProductExportFAQResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class ProductExportResponse(BaseModel):
    items: list[ProductExportItem]


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    category_id: UUID
    image: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    best_seller: bool = False
    stock: bool = True
    stock_count: int = Field(0, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    specs: Optional[ProductSpecCreate] = None
    faqs: Optional[list[ProductFAQCreate]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, decimal_places=2)
    category_id: Optional[UUID] = None
    image: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    best_seller: Optional[bool] = None
    stock: Optional[bool] = None
    stock_count: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    specs: Optional[ProductSpecUpdate] = None
    faqs: Optional[list[ProductFAQUpdate]] = None


class ProductListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    price: Decimal
    category_id: UUID
    image: Optional[str] = None
    short_description: Optional[str] = None
    discount_price: Optional[Decimal] = None
    best_seller: bool = False
    stock: bool
    stock_count: int
    sku: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductBulkItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    category_id: UUID
    image: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    best_seller: bool = False
    stock: bool = True
    stock_count: int = Field(0, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    specs: Optional[ProductSpecCreate] = None
    faqs: Optional[list[ProductFAQCreate]] = None


class ProductBulkRequest(BaseModel):
    items: list[ProductBulkItem] = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def check_duplicate_names(self):
        names = [item.name.strip().lower() for item in self.items]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate product names found in the request")
        return self


class BulkErrorDetail(BaseModel):
    index: int
    name: str
    error: str


class ProductBulkResponse(BaseModel):
    created: int
    errors: list[BulkErrorDetail]
    products: list[ProductDetailResponse]


class ProductDetailResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    best_seller: bool = False
    category_id: UUID
    image: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    stock: bool
    stock_count: int
    sku: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None
    specs: Optional[ProductSpecResponse] = None
    faqs: Optional[list[ProductFAQResponse]] = None

    model_config = ConfigDict(from_attributes=True)
