from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.security import verify_admin_token
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(data: LoginRequest) -> LoginResponse:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={
                "email": data.email,
                "password": data.password,
            },
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    body = response.json()

    return LoginResponse(
        access_token=body["access_token"],
        token_type="bearer",
        user=body.get("user"),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> RegisterResponse:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            json={
                "email": data.email,
                "password": data.password,
                "user_metadata": {
                    "role": "admin",
                    "name": data.name or data.email.split("@")[0],
                },
                "email_confirm": True,
            },
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
            },
        )

    if response.status_code != 200:
        detail = response.json().get("msg", "Failed to create user")
        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    body = response.json()

    return RegisterResponse(
        id=body["id"],
        email=body["email"],
        role=body["user_metadata"]["role"],
        created_at=body["created_at"],
    )
