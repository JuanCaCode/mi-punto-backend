"""Prueba de integracion #2 — Ciclo de vida de un negocio.

Cubre la creacion/edicion por el admin, la geolocalizacion y busqueda por
cercania (PostGIS), el catalogo publico, el detalle (registro de visita), la
gestion global del owner y las metricas del owner.
"""

import pytest

from app.modules.auth.models import UserRole

pytestmark = pytest.mark.integration


def test_ciclo_de_vida_de_negocio(client, db_session, factories):
    category = factories.category(db_session, name="Cafetería", slug="cafeteria")
    admin = factories.user(db_session, email="admin@demo.com", role=UserRole.business_admin)
    owner = factories.user(db_session, email="owner@demo.com", role=UserRole.owner)
    admin_h = factories.auth_headers(admin)
    owner_h = factories.auth_headers(owner)

    # 1) El admin crea su negocio.
    create = client.post(
        "/businesses/me",
        headers=admin_h,
        json={
            "name": "Café Aroma",
            "description": "Café de origen",
            "category_id": category.id,
            "city": "Bogotá",
            "address": "Calle 72 #10-34",
            "instagram_url": "instagram.com/cafearoma",
        },
    )
    assert create.status_code == 201
    business_id = create.json()["id"]
    assert create.json()["instagram_url"] == "https://instagram.com/cafearoma"

    # 2) No puede crear un segundo negocio.
    dup = client.post(
        "/businesses/me",
        headers=admin_h,
        json={"name": "Otro", "category_id": category.id, "city": "Bogotá"},
    )
    assert dup.status_code == 409

    # 3) Ciudad invalida → 400.
    bad_city = client.put(
        "/businesses/me",
        headers=admin_h,
        json={"city": "Ciudad Falsa"},
    )
    assert bad_city.status_code == 400

    # 4) Categoria invalida → 400.
    bad_cat = client.put(
        "/businesses/me",
        headers=admin_h,
        json={"category_id": 99999},
    )
    assert bad_cat.status_code == 400

    # 5) Edicion valida.
    upd = client.put(
        "/businesses/me",
        headers=admin_h,
        json={"name": "Café Aroma Centro", "city": "Medellín"},
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Café Aroma Centro"
    assert upd.json()["city"] == "Medellín"

    # 6) Set de ubicacion (PostGIS).
    loc = client.put(
        "/businesses/me/location",
        headers=admin_h,
        json={"lat": 6.2087, "lng": -75.5712, "address": "Calle 10"},
    )
    assert loc.status_code == 200
    assert loc.json()["lat"] == pytest.approx(6.2087, abs=1e-3)

    # 7) GET de su propio negocio.
    mine = client.get("/businesses/me", headers=admin_h)
    assert mine.status_code == 200 and mine.json()["id"] == business_id

    # 8) Catalogo publico lista el negocio activo (filtrando por ciudad).
    catalog = client.get("/businesses", params={"city": "Medellín"})
    assert catalog.status_code == 200
    assert any(b["id"] == business_id for b in catalog.json())

    # 9) Busqueda por cercania (PostGIS ST_DWithin).
    nearby = client.get(
        "/businesses/nearby",
        params={"lat": 6.2087, "lng": -75.5712, "radius_km": 5},
    )
    assert nearby.status_code == 200
    assert any(b["id"] == business_id for b in nearby.json())
    near_row = next(b for b in nearby.json() if b["id"] == business_id)
    assert near_row["distance_km"] is not None

    # 10) Detalle publico (registra visita).
    detail = client.get(f"/businesses/{business_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "Café Aroma Centro"

    # 11) Owner: tabla global + detalle + metricas.
    admin_list = client.get("/businesses/admin", headers=owner_h)
    assert admin_list.status_code == 200 and len(admin_list.json()) >= 1

    owner_detail = client.get(f"/businesses/{business_id}/admin", headers=owner_h)
    assert owner_detail.status_code == 200
    assert owner_detail.json()["profile_views"] >= 1  # la visita del paso 10

    metrics = client.get("/metrics/owner", headers=owner_h)
    assert metrics.status_code == 200
    assert metrics.json()["total_businesses"] >= 1

    # 12) Owner desactiva el negocio → el detalle publico pasa a 404.
    toggle = client.patch(f"/businesses/{business_id}/toggle", headers=owner_h)
    assert toggle.status_code == 200 and toggle.json()["is_active"] is False
    assert client.get(f"/businesses/{business_id}").status_code == 404


def test_un_admin_no_puede_ver_endpoints_de_owner(client, db_session, factories):
    admin = factories.user(db_session, email="admin2@demo.com", role=UserRole.business_admin)
    resp = client.get("/businesses/admin", headers=factories.auth_headers(admin))
    assert resp.status_code == 403
