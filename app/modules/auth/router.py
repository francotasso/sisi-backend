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
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
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
                    "role": data.role,
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


@router.get("/users")
async def list_users(
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> UserListResponse:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch users",
        )

    users_raw = response.json().get("users", [])
    users = [
        UserResponse(
            id=u["id"],
            email=u["email"],
            role=u.get("user_metadata", {}).get("role", "authenticated"),
            name=u.get("user_metadata", {}).get("name"),
            created_at=u["created_at"],
            last_sign_in_at=u.get("last_sign_in_at"),
            phone=u.get("phone"),
        )
        for u in users_raw
    ]
    return UserListResponse(users=users)


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> dict:
    payload = data.model_dump(exclude_none=True)
    has_name = "name" in payload
    if has_name:
        name = payload.pop("name")

        if "user_metadata" not in payload:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail="Failed to fetch user metadata",
                )
            current_meta = resp.json().get("raw_user_meta_data", {})
            payload["user_metadata"] = current_meta

        payload["user_metadata"]["name"] = name

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            json=payload,
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
            },
        )

    if response.status_code != 200:
        detail = response.json().get("msg", "Failed to update user")
        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    return response.json()


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    admin: Annotated[dict, Depends(verify_admin_token)],
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
        )

    if response.status_code not in (200, 204):
        detail = response.json().get("msg", "Failed to delete user")
        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    return {"message": "User deleted successfully"}
