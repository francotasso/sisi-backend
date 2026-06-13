import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            )
            _jwks_cache = response.json()
    return _jwks_cache


async def _verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    token = credentials.credentials
    payload = None

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        pass

    if payload is None:
        try:
            jwks = await _get_jwks()
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
        except JWTError:
            pass

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = await _verify_token(credentials)
    role = payload.get("user_metadata", {}).get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return payload


async def verify_editor_access(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = await _verify_token(credentials)
    role = payload.get("user_metadata", {}).get("role")
    if role not in ("admin", "editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or editor role required",
        )
    return payload
