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
    role: str = Field(default="admin", pattern="^(admin|editor)$")


class RegisterResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: str
    message: str = "User created successfully"


class UserUpdateRequest(BaseModel):
    email: str | None = Field(None, max_length=255)
    password: str | None = Field(None, min_length=6)
    name: str | None = None
    user_metadata: dict | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    name: str | None = None
    created_at: str
    last_sign_in_at: str | None = None
    phone: str | None = None


class UserListResponse(BaseModel):
    users: list[UserResponse]
