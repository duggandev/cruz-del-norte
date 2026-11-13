from app.sc01_viajes.routes import router
from app.shared.app_factory import create_app

app = create_app("SC-01 Disponibilidad Viajes")
app.include_router(router)
