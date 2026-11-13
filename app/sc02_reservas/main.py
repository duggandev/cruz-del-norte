from app.sc02_reservas.routes import router
from app.shared.app_factory import create_app

app = create_app("SC-02 - Gestión de Reservas")
app.include_router(router)
