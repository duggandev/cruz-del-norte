from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.sc01_viajes import repository
from app.shared.errors import ApiError


LIMA = ZoneInfo("America/Lima")


def consultar_disponibilidad(db: Session, origen: str, destino: str, fecha: date) -> dict | None:
    origen = origen.strip()
    destino = destino.strip()
    if not origen or not destino:
        raise ApiError(400, "Origen y destino son obligatorios.")
    if origen.casefold() == destino.casefold():
        raise ApiError(400, "Origen y destino deben ser diferentes.")
    try:
        viajes = repository.find_viajes(db, origen, destino, fecha)
        if not viajes:
            return None
        ahora = datetime.now(LIMA).replace(tzinfo=None)
        return {
            "origen": origen,
            "destino": destino,
            "fecha": fecha.isoformat(),
            "viajes": [
                {
                    "idViaje": viaje.id_viaje,
                    "horaSalida": viaje.hora_salida,
                    "tarifa": float(Decimal(viaje.tarifa_centavos) / 100),
                    "asientosDisponibles": repository.find_asientos_disponibles(db, viaje.id_viaje, ahora),
                }
                for viaje in viajes
            ],
        }
    except OperationalError as exc:
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc
