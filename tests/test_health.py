"""Pruebas de humo del API.

No requieren conexion a la base de datos: validan que la aplicacion
arranca correctamente y que los endpoints de salud responden.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_disponible():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Mi Punto API"
