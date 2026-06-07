"""Prueba de integracion #1 — Flujo de autenticacion.

Cubre el registro, el login (exito y fallos) y el acceso al perfil con token,
ejercitando auth/service contra una base de datos PostGIS real.
"""

import pytest

from app.modules.auth.models import UserRole

pytestmark = pytest.mark.integration


def test_flujo_completo_de_autenticacion(client, db_session, factories):
    # 1) Registro de un usuario final.
    resp = client.post(
        "/auth/register",
        json={
            "email": "nuevo@demo.com",
            "password": "password123",
            "full_name": "Usuario Nuevo",
            "role": "end_user",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "nuevo@demo.com"
    assert body["role"] == "end_user"

    # 2) Registrar el mismo email otra vez → conflicto.
    dup = client.post(
        "/auth/register",
        json={
            "email": "nuevo@demo.com",
            "password": "password123",
            "full_name": "Otro",
        },
    )
    assert dup.status_code == 409

    # 3) Login con password incorrecta → 401.
    bad = client.post(
        "/auth/login",
        json={"email": "nuevo@demo.com", "password": "incorrecta"},
    )
    assert bad.status_code == 401

    # 4) Login correcto → token + datos del usuario.
    ok = client.post(
        "/auth/login",
        json={"email": "nuevo@demo.com", "password": "password123"},
    )
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    assert ok.json()["token_type"] == "bearer"

    # 5) Acceso a /auth/me con el token.
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "nuevo@demo.com"

    # 6) /auth/me sin token → 401.
    assert client.get("/auth/me").status_code == 401


def test_login_de_usuario_desactivado_es_rechazado(client, db_session, factories):
    factories.user(
        db_session,
        email="inactivo@demo.com",
        password="password123",
        is_active=False,
        role=UserRole.end_user,
    )
    resp = client.post(
        "/auth/login",
        json={"email": "inactivo@demo.com", "password": "password123"},
    )
    assert resp.status_code == 403
