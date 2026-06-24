from uuid import UUID

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_editor_access
from app.modules.products.schemas import (
    ProductBulkRequest,
    ProductBulkResponse,
    ProductCardResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductExportResponse,
    ProductUpdate,
)
from app.modules.products.service import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    category: Annotated[Optional[str], Query(description="Category slug")] = None,
    price_min: Annotated[Optional[float], Query(ge=0)] = None,
    price_max: Annotated[Optional[float], Query(ge=0)] = None,
    stock: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query(min_length=1)] = None,
    sort_by: Annotated[Optional[str], Query(pattern="^(price|name|created_at)$")] = None,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
):
    return await product_service.get_list(
        db,
        skip=skip,
        limit=limit,
        category_slug=category,
        price_min=price_min,
        price_max=price_max,
        stock=stock,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/newest")
async def get_newest_products(
    limit: Annotated[int, Query(ge=1, le=50)] = 4,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[ProductCardResponse]:
    return await product_service.get_newest(db, limit)


@router.get("/best-sellers")
async def get_best_sellers(
    limit: Annotated[int, Query(ge=1, le=50)] = 4,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[ProductCardResponse]:
    return await product_service.get_best_sellers(db, limit)


@router.get("/export")
async def export_products(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductExportResponse:
    return await product_service.export_all(db)


@router.get("/batch")
async def get_products_batch(
    slugs: Annotated[str, Query(description="Comma-separated list of product slugs")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProductCardResponse]:
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    if not slug_list:
        return []
    return await product_service.get_by_slugs(db, slug_list)


@router.get("/{slug}")
async def get_product(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductDetailResponse:
    return await product_service.get_by_slug(db, slug)


@router.put("/bulk", status_code=status.HTTP_200_OK)
async def replace_all_products(
    data: ProductBulkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_editor_access)],
) -> ProductBulkResponse:
    return await product_service.replace_all(db, data)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_products(
    data: ProductBulkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_editor_access)],
) -> ProductBulkResponse:
    return await product_service.bulk_create(db, data)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_editor_access)],
) -> ProductDetailResponse:
    return await product_service.create(db, data)


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_editor_access)],
) -> ProductDetailResponse:
    return await product_service.update(db, product_id, data)


@router.post("/{product_id}/image")
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    admin: Annotated[dict, Depends(verify_editor_access)] = None,
) -> ProductDetailResponse:
    return await product_service.upload_image(db, product_id, file)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_editor_access)],
) -> None:
    await product_service.soft_delete(db, product_id)
