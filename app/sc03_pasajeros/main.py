from app.sc03_pasajeros.routes import router
from app.shared.app_factory import create_app

app = create_app("SC-03 Validación Pasajeros")
app.include_router(router)
