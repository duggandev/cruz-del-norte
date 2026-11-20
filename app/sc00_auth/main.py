from app.shared.app_factory import create_app
from app.sc00_auth.routes import router

app = create_app("Servicio de Autenticacion")
app.include_router(router)
