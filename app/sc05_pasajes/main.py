from fastapi.staticfiles import StaticFiles

from app.sc05_pasajes.routes import router
from app.shared.app_factory import create_app
from app.shared.config import settings

settings.pasajes_directory.mkdir(parents=True, exist_ok=True)
app = create_app("SC-05 - Emisión de Pasajes")
app.include_router(router)
app.mount("/documentos", StaticFiles(directory=str(settings.pasajes_directory)), name="documentos")
