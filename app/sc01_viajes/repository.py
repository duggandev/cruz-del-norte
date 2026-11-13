from datetime import date, datetime

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session

from app.shared.models import AsientoViaje, Reserva, Viaje


def find_viajes(db: Session, origen: str, destino: str, fecha: date) -> list[Viaje]:
    return list(db.scalars(
        select(Viaje).where(
            Viaje.origen.collate("NOCASE") == origen,
            Viaje.destino.collate("NOCASE") == destino,
            Viaje.fecha == fecha,
            Viaje.estado.in_(("PROGRAMADO", "DISPONIBLE")),
        ).order_by(Viaje.hora_salida)
    ))


def find_asientos_disponibles(db: Session, id_viaje: int, ahora_local: datetime) -> list[int]:
    bloqueada = exists().where(
        Reserva.id_viaje == AsientoViaje.id_viaje,
        Reserva.id_asiento == AsientoViaje.id_asiento,
        or_(
            Reserva.estado == "CONFIRMADA",
            and_(Reserva.estado == "TEMPORAL", Reserva.vencimiento > ahora_local),
        ),
    )
    return list(db.scalars(
        select(AsientoViaje.id_asiento).where(
            AsientoViaje.id_viaje == id_viaje,
            AsientoViaje.estado == "DISPONIBLE",
            ~bloqueada,
        ).order_by(AsientoViaje.id_asiento)
    ))
