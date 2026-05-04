from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    full_name: str | None = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str