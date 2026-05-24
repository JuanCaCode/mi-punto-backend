from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_social_url(value: Optional[str], allowed_hosts: tuple[str, ...], label: str) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"URL de {label} inválida")

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if not any(host == h or host.endswith("." + h) for h in allowed_hosts):
        raise ValueError(
            f"La URL de {label} debe apuntar a {' o '.join(allowed_hosts)}"
        )
    return cleaned


_INSTAGRAM_HOSTS = ("instagram.com", "instagr.am")
_FACEBOOK_HOSTS = ("facebook.com", "fb.com", "fb.me", "m.facebook.com")


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class MediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    is_primary: bool
    sort_order: int


class BusinessSummary(BaseModel):
    """Listado para usuario / dueño."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    city: str
    address: str
    is_active: bool
    category: CategoryOut
    cover_url: Optional[str] = None
    logo_url: Optional[str] = None
    average_rating: float = 0.0
    review_count: int = 0
    distance_km: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class BusinessOwnerRow(BaseModel):
    """Fila de la tabla del owner global."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    is_active: bool
    category_name: str
    admin_full_name: str
    admin_email: str


class BusinessDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    city: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Optional[str] = None
    is_active: bool
    category: CategoryOut
    cover_url: Optional[str] = None
    logo_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    media: list[MediaOut] = []
    average_rating: float = 0.0
    review_count: int = 0
    profile_views: int = 0
    lat: Optional[float] = None
    lng: Optional[float] = None
    admin_full_name: Optional[str] = None
    admin_email: Optional[str] = None
    created_at: datetime


class ToggleResult(BaseModel):
    id: int
    is_active: bool


# ----- Admin (su propio negocio) -----

class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    category_id: int
    city: str = Field(min_length=2, max_length=80)
    address: str = Field(default="", max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    email: Optional[str] = Field(default=None, max_length=160)
    hours: Optional[str] = Field(default=None, max_length=255)
    instagram_url: Optional[str] = Field(default=None, max_length=255)
    facebook_url: Optional[str] = Field(default=None, max_length=255)

    @field_validator("instagram_url")
    @classmethod
    def _validate_instagram(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_social_url(v, _INSTAGRAM_HOSTS, "Instagram")

    @field_validator("facebook_url")
    @classmethod
    def _validate_facebook(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_social_url(v, _FACEBOOK_HOSTS, "Facebook")


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2000)
    category_id: Optional[int] = None
    city: Optional[str] = Field(default=None, min_length=2, max_length=80)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    email: Optional[str] = Field(default=None, max_length=160)
    hours: Optional[str] = Field(default=None, max_length=255)
    instagram_url: Optional[str] = Field(default=None, max_length=255)
    facebook_url: Optional[str] = Field(default=None, max_length=255)

    @field_validator("instagram_url")
    @classmethod
    def _validate_instagram(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_social_url(v, _INSTAGRAM_HOSTS, "Instagram")

    @field_validator("facebook_url")
    @classmethod
    def _validate_facebook(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_social_url(v, _FACEBOOK_HOSTS, "Facebook")


class BusinessLocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=255)


class PublicBusinessSummary(BaseModel):
    """Tarjeta del catálogo público y del mapa."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    city: str
    address: str
    category: CategoryOut
    cover_url: Optional[str] = None
    logo_url: Optional[str] = None
    average_rating: float = 0.0
    review_count: int = 0
    lat: Optional[float] = None
    lng: Optional[float] = None
    distance_km: Optional[float] = None


class PublicBusinessDetail(BaseModel):
    """Vista detallada para el usuario final."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    city: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Optional[str] = None
    category: CategoryOut
    cover_url: Optional[str] = None
    logo_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    media: list[MediaOut] = []
    average_rating: float = 0.0
    review_count: int = 0
    lat: Optional[float] = None
    lng: Optional[float] = None


class MyBusinessOut(BaseModel):
    """Vista completa que el admin obtiene de su propio negocio."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    city: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Optional[str] = None
    is_active: bool
    category: CategoryOut
    cover_url: Optional[str] = None
    logo_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    media: list[MediaOut] = []
    lat: Optional[float] = None
    lng: Optional[float] = None
    average_rating: float = 0.0
    review_count: int = 0
    profile_views: int = 0
