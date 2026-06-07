"""Pruebas unitarias de la configuracion (normalizacion de URL y CORS)."""

from pathlib import Path

from app.core.config import Settings


def test_normaliza_postgresql_a_psycopg():
    s = Settings(DATABASE_URL="postgresql://u:p@host:5432/db")
    assert s.sqlalchemy_database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_normaliza_postgres_a_psycopg():
    s = Settings(DATABASE_URL="postgres://u:p@host:5432/db")
    assert s.sqlalchemy_database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_no_modifica_url_que_ya_trae_driver():
    url = "postgresql+psycopg://u:p@host:5432/db"
    s = Settings(DATABASE_URL=url)
    assert s.sqlalchemy_database_url == url


def test_cors_origins_list_parsea_y_limpia():
    s = Settings(CORS_ORIGINS="http://a.com, http://b.com ,, ")
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


def test_upload_path_es_absoluto():
    s = Settings(UPLOAD_DIR="./uploads")
    assert isinstance(s.upload_path, Path)
    assert s.upload_path.is_absolute()
