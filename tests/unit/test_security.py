"""Pruebas unitarias del modulo de seguridad (hashing y JWT)."""

import pytest

from app.core import security


def test_hash_password_no_es_texto_plano():
    hashed = security.hash_password("secret123")
    assert hashed != "secret123"
    assert hashed.startswith("$2")  # prefijo bcrypt


def test_verify_password_correcta_e_incorrecta():
    hashed = security.hash_password("secret123")
    assert security.verify_password("secret123", hashed) is True
    assert security.verify_password("otra-clave", hashed) is False


def test_verify_password_hash_invalido_devuelve_false():
    # Un hash mal formado no debe lanzar excepcion, debe devolver False.
    assert security.verify_password("x", "no-es-un-hash") is False


def test_password_mayor_a_72_bytes_se_trunca():
    # bcrypt opera sobre 72 bytes; passwords largas no deben romper.
    larga = "a" * 100
    hashed = security.hash_password(larga)
    assert security.verify_password("a" * 100, hashed) is True


def test_create_y_decode_token_roundtrip():
    token = security.create_access_token(subject="42", extra_claims={"role": "owner"})
    payload = security.decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "owner"
    assert "exp" in payload


def test_decode_token_invalido_lanza_valueerror():
    with pytest.raises(ValueError):
        security.decode_token("token.invalido.xxx")
