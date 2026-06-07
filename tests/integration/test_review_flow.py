"""Prueba de integracion #3 — Reseñas y respuestas.

Cubre la publicacion de reseñas por el usuario final, las reglas de negocio
(no reseñar dos veces, no reseñar negocio propio), la respuesta del admin,
el listado del negocio, las reseñas del usuario y las metricas del negocio.
"""

import pytest

from app.modules.auth.models import UserRole
from app.modules.reviews import service as reviews_service
from app.modules.reviews.schemas import ReviewCreate

pytestmark = pytest.mark.integration


def test_flujo_de_reseñas_y_respuesta(client, db_session, factories):
    category = factories.category(db_session, slug="restaurante", name="Restaurante")
    admin = factories.user(db_session, email="admin@demo.com", role=UserRole.business_admin)
    business = factories.business(db_session, owner=admin, category=category, name="El Sabor")
    user = factories.user(db_session, email="user@demo.com", role=UserRole.end_user)
    user_h = factories.auth_headers(user)
    admin_h = factories.auth_headers(admin)

    # 1) El usuario publica una reseña.
    create = client.post(
        f"/businesses/{business.id}/reviews",
        headers=user_h,
        json={"rating": 5, "comment": "Excelente comida"},
    )
    assert create.status_code == 201
    review_id = create.json()["id"]

    # 2) No puede reseñar dos veces el mismo negocio.
    dup = client.post(
        f"/businesses/{business.id}/reviews",
        headers=user_h,
        json={"rating": 3, "comment": "Otra vez"},
    )
    assert dup.status_code == 409

    # 3) Reseñar un negocio inexistente → 404.
    nf = client.post(
        "/businesses/999999/reviews",
        headers=user_h,
        json={"rating": 4, "comment": "No existe"},
    )
    assert nf.status_code == 404

    # 4) Listado publico de reseñas del negocio.
    listing = client.get(f"/businesses/{business.id}/reviews")
    assert listing.status_code == 200
    assert any(r["id"] == review_id for r in listing.json())

    # 5) El admin responde la reseña.
    response = client.post(
        f"/reviews/{review_id}/response",
        headers=admin_h,
        json={"body": "¡Gracias por tu visita!"},
    )
    assert response.status_code == 200
    assert response.json()["response"]["body"] == "¡Gracias por tu visita!"

    # 6) Responder de nuevo actualiza (no duplica).
    response2 = client.post(
        f"/reviews/{review_id}/response",
        headers=admin_h,
        json={"body": "Texto actualizado"},
    )
    assert response2.status_code == 200
    assert response2.json()["response"]["body"] == "Texto actualizado"

    # 7) Un admin ajeno no puede responder.
    other_admin = factories.user(db_session, email="otro@demo.com", role=UserRole.business_admin)
    forbidden = client.post(
        f"/reviews/{review_id}/response",
        headers=factories.auth_headers(other_admin),
        json={"body": "Intruso"},
    )
    assert forbidden.status_code == 403

    # 8) Reseñas del usuario.
    mine = client.get("/users/me/reviews", headers=user_h)
    assert mine.status_code == 200
    assert mine.json()[0]["business_name"] == "El Sabor"

    # 9) Metricas del negocio del admin.
    metrics = client.get("/metrics/business/me", headers=admin_h)
    assert metrics.status_code == 200
    assert metrics.json()["total_reviews"] == 1
    assert metrics.json()["response_rate"] == 100.0


def test_no_se_puede_reseñar_negocio_propio(client, db_session, factories):
    # Regla de negocio a nivel de servicio: el dueño no puede reseñar su negocio.
    category = factories.category(db_session, slug="tienda", name="Tienda")
    admin = factories.user(db_session, email="duenio@demo.com", role=UserRole.business_admin)
    business = factories.business(db_session, owner=admin, category=category)

    with pytest.raises(Exception) as exc:
        reviews_service.create_review(
            db_session, business.id, admin, ReviewCreate(rating=5, comment="Mi propio negocio")
        )
    assert "own business" in str(exc.value)
