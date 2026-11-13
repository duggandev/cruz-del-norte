from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.shared.models import AsientoViaje, Pago, Reserva, Viaje


def get_viaje(db: Session, id_viaje: int) -> Viaje | None:
    return db.get(Viaje, id_viaje)


def get_asiento(db: Session, id_viaje: int, id_asiento: int) -> AsientoViaje | None:
    return db.get(AsientoViaje, (id_viaje, id_asiento))


def expirar_reservas(db: Session, ahora: datetime) -> None:
    db.execute(
        update(Reserva)
        .where(Reserva.estado == "TEMPORAL", Reserva.vencimiento <= ahora)
        .values(estado="VENCIDA")
    )


def get_bloqueo(db: Session, id_viaje: int, id_asiento: int) -> Reserva | None:
    return db.scalar(select(Reserva).where(
        Reserva.id_viaje == id_viaje,
        Reserva.id_asiento == id_asiento,
        Reserva.estado.in_(("TEMPORAL", "CONFIRMADA")),
    ))


def get_reserva(db: Session, id_reserva: int) -> Reserva | None:
    return db.get(Reserva, id_reserva)


def tiene_pago_aprobado(db: Session, id_reserva: int) -> bool:
    return db.scalar(select(Pago.id_pago).where(Pago.id_reserva == id_reserva, Pago.estado == "APROBADO").limit(1)) is not None
