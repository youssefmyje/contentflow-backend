from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
        examples=["Youssef"],
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
        examples=["Benali"],
    )

    email: EmailStr = Field(
        examples=["youssef@example.com"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["MotDePasse123!"],
    )


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    auth_provider: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["MotDePasse123!"],
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse