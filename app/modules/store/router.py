from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_admin_token
from app.modules.store.schemas import StoreCreate, StoreResponse, StoreUpdate
from app.modules.store.service import store_service

router = APIRouter(prefix="/store", tags=["store"])


@router.get("")
async def get_store(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StoreResponse:
    return await store_service.get(db)


@router.post("")
async def create_store(
    data: StoreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> StoreResponse:
    return await store_service.create(db, data)


@router.put("")
async def update_store(
    data: StoreUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> StoreResponse:
    return await store_service.update(db, data)
