from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_admin_token
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.modules.categories.service import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryResponse]:
    return await category_service.get_all(db)


@router.get("/{category_id}")
async def get_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    return await category_service.get_by_id(db, category_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> CategoryResponse:
    return await category_service.create(db, data)


@router.put("/{category_id}")
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> CategoryResponse:
    return await category_service.update(db, category_id, data)


@router.post("/{category_id}/image")
async def upload_category_image(
    category_id: UUID,
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    admin: Annotated[dict, Depends(verify_admin_token)] = None,
) -> CategoryResponse:
    return await category_service.upload_image(db, category_id, file)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> None:
    await category_service.delete(db, category_id)
