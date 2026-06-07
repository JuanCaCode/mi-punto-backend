from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+psycopg://mipunto:mipunto@localhost:5432/mi_punto"
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    UPLOAD_DIR: str = "./uploads"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL normalizada para SQLAlchemy.

        Proveedores como Render entregan la URL con el esquema
        ``postgresql://`` (o ``postgres://``); aqui se fuerza el driver
        ``psycopg`` (v3), que es el instalado en requirements.txt.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR).resolve()


settings = Settings()
