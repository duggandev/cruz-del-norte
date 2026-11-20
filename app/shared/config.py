from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    database_path: str = "./data/cruz_del_norte.db"
    database_url: str | None = None
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    payment_provider: str = "culqi"
    payment_mock_enabled: bool = False
    public_pasajes_url: str = "http://localhost:8085/documentos"
    storage_pasajes_path: str = "./storage/pasajes"
    reservation_ttl_minutes: int = 25
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:4200,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:4200,http://127.0.0.1:8080,http://178.105.247.228:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (ROOT_DIR / path).resolve()

    @property
    def database_file(self) -> Path:
        return self.resolve_path(self.database_path)

    @property
    def pasajes_directory(self) -> Path:
        return self.resolve_path(self.storage_pasajes_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
