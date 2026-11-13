from app.sc04_pagos.routes import router
from app.shared.app_factory import create_app

app = create_app("SC-04 - Gestión de Pagos")
app.include_router(router)
