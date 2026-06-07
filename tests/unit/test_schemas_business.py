"""Pruebas unitarias de los esquemas de negocio (normalizacion de redes sociales)."""

import pytest
from pydantic import ValidationError

from app.modules.businesses.schemas import BusinessCreate, BusinessLocationUpdate


def _create(**kwargs) -> BusinessCreate:
    base = {"name": "Mi Negocio", "category_id": 1, "city": "Bogotá"}
    base.update(kwargs)
    return BusinessCreate(**base)


def test_instagram_agrega_https():
    b = _create(instagram_url="instagram.com/minegocio")
    assert b.instagram_url == "https://instagram.com/minegocio"


def test_instagram_acepta_subdominio_y_www():
    b = _create(instagram_url="https://www.instagram.com/mi")
    assert b.instagram_url.startswith("https://www.instagram.com/")


def test_instagram_host_invalido_falla():
    with pytest.raises(ValidationError):
        _create(instagram_url="https://tiktok.com/mi")


def test_facebook_valido():
    b = _create(facebook_url="fb.com/mipagina")
    assert b.facebook_url == "https://fb.com/mipagina"


def test_redes_vacias_quedan_none():
    b = _create(instagram_url="", facebook_url="   ")
    assert b.instagram_url is None
    assert b.facebook_url is None


def test_url_sin_host_falla():
    with pytest.raises(ValidationError):
        _create(facebook_url="https://")


def test_nombre_muy_corto_falla():
    with pytest.raises(ValidationError):
        _create(name="x")


def test_location_update_fuera_de_rango_falla():
    with pytest.raises(ValidationError):
        BusinessLocationUpdate(lat=200, lng=0)
    with pytest.raises(ValidationError):
        BusinessLocationUpdate(lat=0, lng=999)


def test_location_update_valida():
    loc = BusinessLocationUpdate(lat=4.6, lng=-74.0, address="Calle 1")
    assert loc.lat == 4.6 and loc.lng == -74.0
