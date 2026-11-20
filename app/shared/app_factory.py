from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.errors import enforce_media_types, install_error_handlers
from app.shared.config import settings


def create_app(title: str, version: str = "1.0.0") -> FastAPI:
    app = FastAPI(title=title, version=version)
    origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
    # Origen de la web alojada en el servidor del cliente; se conserva aunque
    # Coolify sobrescriba CORS_ALLOWED_ORIGINS con una variable propia.
    if "http://178.105.247.228:8000" not in origins:
        origins.append("http://178.105.247.228:8000")
    if "https://appcruzdelnorte.duckdns.org" not in origins:
        origins.append("https://appcruzdelnorte.duckdns.org")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

    @app.get("/health", tags=["Health"], summary="Comprobar estado del servicio")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.middleware("http")(enforce_media_types)
    install_error_handlers(app)
    return app
