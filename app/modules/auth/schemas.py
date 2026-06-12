from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict | None = None


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)
    name: str | None = None


class RegisterResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: str
    message: str = "User created successfully"
