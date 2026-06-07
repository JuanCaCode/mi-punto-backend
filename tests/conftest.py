"""Configuracion compartida de pruebas.

Define la base de datos de prueba (PostGIS), el aislamiento por test
(cada test corre dentro de una transaccion que se revierte al terminar) y
fixtures de cliente HTTP y de autenticacion.

La URL de la base de prueba se toma de TEST_DATABASE_URL; por defecto apunta
al contenedor local de docker-compose (puerto 5433, base mi_punto_test).
"""

import os

# IMPORTANTE: fijar la base de datos de prueba ANTES de importar la app,
# para que el engine se construya apuntando a la base correcta y nunca a
# la base de desarrollo/produccion.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://mipunto:mipunto@localhost:5433/mi_punto_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import Base, engine, get_db  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.modules.auth.models import User, UserRole  # noqa: E402
from app.modules.businesses.models import Business, Category  # noqa: E402

# Importar app.main al final: registra todos los routers (y por ende todos los
# modelos en Base.metadata). Se hace de ultimo para no re-vincular el nombre `app`.
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _setup_database():
    """Crea la extension PostGIS y todas las tablas una vez por sesion.

    No es autouse: solo se activa cuando un test usa db_session/client (los de
    integracion). Asi las pruebas unitarias corren sin necesidad de base de datos.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(_setup_database) -> Session:
    """Sesion aislada: todo lo que ocurra se revierte al final del test.

    Se usa una conexion con una transaccion externa; la sesion crea
    savepoints para los commit() internos de los servicios, de modo que el
    rollback final deja la base limpia entre tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """Cliente HTTP con la dependencia get_db apuntando a la sesion de prueba."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------- Factories de datos ----------

def make_user(
    db: Session,
    *,
    email: str,
    role: UserRole = UserRole.end_user,
    password: str = "password123",
    full_name: str = "Test User",
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_category(db: Session, *, name: str = "Cafetería", slug: str = "cafeteria") -> Category:
    category = Category(name=name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def make_business(
    db: Session,
    *,
    owner: User,
    category: Category,
    name: str = "Café Aroma",
    city: str = "Bogotá",
    is_active: bool = True,
    lat: float | None = 4.6533,
    lng: float | None = -74.0836,
) -> Business:
    business = Business(
        owner_id=owner.id,
        name=name,
        description="Un negocio de prueba",
        category_id=category.id,
        city=city,
        address="Calle 1 #2-3",
        is_active=is_active,
        location=f"SRID=4326;POINT({lng} {lat})" if lat is not None else None,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def auth_headers(user: User) -> dict[str, str]:
    """Genera un header Authorization Bearer valido para el usuario dado."""
    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def factories():
    """Expone las factories como un objeto simple para usarlas en los tests."""
    return type(
        "Factories",
        (),
        {
            "user": staticmethod(make_user),
            "category": staticmethod(make_category),
            "business": staticmethod(make_business),
            "auth_headers": staticmethod(auth_headers),
        },
    )
