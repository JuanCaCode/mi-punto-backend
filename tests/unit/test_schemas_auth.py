"""Pruebas unitarias de los esquemas de autenticacion."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.modules.auth.models import User, UserRole
from app.modules.auth.schemas import UserOut, UserRegister, avatar_public_url


def test_avatar_public_url_none():
    assert avatar_public_url(None) is None
    assert avatar_public_url("") is None


def test_avatar_public_url_construye_url():
    url = avatar_public_url("avatars/user_1.png")
    assert url.endswith("/uploads/avatars/user_1.png")


def test_user_register_rol_por_defecto():
    payload = UserRegister(email="a@b.com", password="password1", full_name="Ana")
    assert payload.role == "end_user"


def test_user_register_password_corta_falla():
    with pytest.raises(ValidationError):
        UserRegister(email="a@b.com", password="corta", full_name="Ana")


def test_user_register_email_invalido_falla():
    with pytest.raises(ValidationError):
        UserRegister(email="no-es-email", password="password1", full_name="Ana")


def test_user_register_rol_no_permitido_falla():
    # owner no puede registrarse por la API publica.
    with pytest.raises(ValidationError):
        UserRegister(email="a@b.com", password="password1", full_name="Ana", role="owner")


def test_user_out_desde_modelo_incluye_avatar_url():
    user = User(
        id=1,
        email="a@b.com",
        full_name="Ana",
        role=UserRole.end_user,
        is_active=True,
        avatar_path="avatars/user_1.png",
        created_at=datetime.now(timezone.utc),
    )
    out = UserOut.model_validate(user)
    assert out.email == "a@b.com"
    assert out.avatar_url.endswith("/uploads/avatars/user_1.png")


def test_user_out_sin_avatar():
    user = User(
        id=2,
        email="c@d.com",
        full_name="Beto",
        role=UserRole.business_admin,
        is_active=True,
        avatar_path=None,
        created_at=datetime.now(timezone.utc),
    )
    out = UserOut.model_validate(user)
    assert out.avatar_url is None
