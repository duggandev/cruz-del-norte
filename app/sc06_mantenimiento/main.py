from app.sc06_mantenimiento.routes import router
from app.shared.app_factory import create_app

app = create_app("SC-06 a SC-10 Mantenimiento y Flota")
app.include_router(router)
