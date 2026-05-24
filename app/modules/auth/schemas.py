from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.config import settings
from app.modules.auth.models import User, UserRole


def avatar_public_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{settings.PUBLIC_BASE_URL}/uploads/{path}"

RegisterRole = Literal["business_admin", "end_user"]


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: RegisterRole = "end_user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    avatar_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _with_avatar_url(cls, data: Any) -> Any:
        if isinstance(data, User):
            return {
                "id": data.id,
                "email": data.email,
                "full_name": data.full_name,
                "role": data.role,
                "is_active": data.is_active,
                "created_at": data.created_at,
                "avatar_url": avatar_public_url(data.avatar_path),
            }
        return data


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
