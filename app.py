"""Punto informativo; cada servicio tiene su propia aplicación ASGI.

Ejecute los módulos indicados en README.md o scripts/start_all.ps1.
"""

SERVICIOS = {
    "AUTH": "app.sc00_auth.main:app (puerto 8087)",
    "SC-01": "app.sc01_viajes.main:app (puerto 8081)",
    "SC-02": "app.sc02_reservas.main:app (puerto 8082)",
    "SC-03": "app.sc03_pasajeros.main:app (puerto 8083)",
    "SC-04": "app.sc04_pagos.main:app (puerto 8084)",
    "SC-05": "app.sc05_pasajes.main:app (puerto 8085)",
    "SC-06": "app.sc06_mantenimiento.main:app (puerto 8086)",
}


if __name__ == "__main__":
    for nombre, comando in SERVICIOS.items():
        print(f"{nombre}: {comando}")
