from fastapi import FastAPI

from app.shared.errors import enforce_media_types, install_error_handlers


def create_app(title: str, version: str = "1.0.0") -> FastAPI:
    app = FastAPI(title=title, version=version)

    @app.get("/health", tags=["Health"], summary="Comprobar estado del servicio")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.middleware("http")(enforce_media_types)
    install_error_handlers(app)
    return app
