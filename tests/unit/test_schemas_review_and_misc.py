"""Pruebas unitarias de esquemas de reseñas, ciudades y helpers de metricas."""

import pytest
from pydantic import ValidationError

from app.modules.metrics.service import _percentage
from app.modules.reviews.schemas import ReviewCreate, ReviewResponseCreate
from app.shared.cities import CITIES


def test_review_rating_valido():
    r = ReviewCreate(rating=5, comment="Excelente lugar")
    assert r.rating == 5


@pytest.mark.parametrize("rating", [0, 6, -1])
def test_review_rating_fuera_de_rango_falla(rating):
    with pytest.raises(ValidationError):
        ReviewCreate(rating=rating, comment="Comentario valido")


def test_review_comentario_muy_corto_falla():
    with pytest.raises(ValidationError):
        ReviewCreate(rating=4, comment="x")


def test_review_response_valida_y_corta():
    assert ReviewResponseCreate(body="Gracias!").body == "Gracias!"
    with pytest.raises(ValidationError):
        ReviewResponseCreate(body="x")


def test_cities_incluye_principales():
    for ciudad in ("Bogotá", "Medellín", "Cali"):
        assert ciudad in CITIES


def test_percentage_total_cero():
    assert _percentage(0, 0) == 0.0


def test_percentage_redondea_a_un_decimal():
    assert _percentage(1, 3) == 33.3
    assert _percentage(1, 4) == 25.0
