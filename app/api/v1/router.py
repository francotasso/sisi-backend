from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.products.router import router as products_router
from app.modules.categories.router import router as categories_router
from app.modules.store.router import router as store_router
from app.modules.testimonials.router import router as testimonials_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(categories_router)
api_router.include_router(store_router)
api_router.include_router(testimonials_router)
