# Pruebas — Backend (Mi Punto API)

## Tipos de prueba

| Tipo | Herramienta | Ubicacion | Que valida |
|---|---|---|---|
| Unitarias | `pytest` | `tests/unit/` | Logica pura: seguridad/JWT, config, validaciones de esquemas, helpers |
| Integracion (3) | `pytest` + PostGIS | `tests/integration/` | Flujos completos contra una base de datos real |
| Coverage | `pytest-cov` | — | Umbral **85%** sobre la capa de logica |

Las **3 pruebas de integracion** son:
1. `test_auth_flow.py` — registro, login (exito/fallos) y perfil.
2. `test_business_flow.py` — ciclo de vida del negocio + geolocalizacion (PostGIS) + metricas del owner.
3. `test_review_flow.py` — reseñas, respuestas del admin y metricas del negocio.

## Coverage

El alcance del 85% es la **capa de logica** (`app/core/security.py`, `app/core/config.py`,
`app/modules/*/service.py`, `app/modules/*/schemas.py`, `app/shared/cities.py`).
Se excluyen routers, modelos, `main.py` e IO de archivos (ver `pyproject.toml`).
Coverage actual: **~95%**.

## Correr las pruebas localmente

Requiere una base de datos PostGIS de prueba. Con el `docker-compose.yml` del repo raiz:

```bash
# 1) Levantar PostGIS (puerto 5433)
docker compose up -d postgis
docker exec mi_punto_postgis psql -U mipunto -d mi_punto -c "CREATE DATABASE mi_punto_test"
docker exec mi_punto_postgis psql -U mipunto -d mi_punto_test -c "CREATE EXTENSION IF NOT EXISTS postgis"

# 2) Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 3) Ejecutar
pytest                                  # toda la suite
pytest -m "not integration"             # solo unitarias (rapido, sin DB)
pytest --cov=app --cov-report=term-missing   # con reporte de coverage
```

La URL de la base de prueba se configura con `TEST_DATABASE_URL`
(por defecto `postgresql+psycopg://mipunto:mipunto@localhost:5433/mi_punto_test`).

## Hooks de pre-commit

En cada `git commit` se corren **lint + pruebas unitarias** (rapido). Instalacion:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## En CI

El workflow `.github/workflows/ci.yml` (job **test**) levanta un PostGIS como
service container, corre toda la suite y **falla si el coverage baja del 85%**.
Las pruebas se ejecutan en cada Pull Request y en cada push a `main`.
