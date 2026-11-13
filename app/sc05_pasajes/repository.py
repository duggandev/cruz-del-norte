from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.models import Pago, Pasaje, Reserva, Viaje


def get_reserva_con_viaje(db: Session, id_reserva: int):
    return db.execute(
        select(Reserva, Viaje).join(Viaje, Reserva.id_viaje == Viaje.id_viaje).where(Reserva.id_reserva == id_reserva)
    ).one_or_none()


def get_pago(db: Session, id_transaccion: str) -> Pago | None:
    return db.scalar(select(Pago).where(Pago.id_transaccion == id_transaccion))


def get_pasaje(db: Session, id_reserva: int) -> Pasaje | None:
    return db.scalar(select(Pasaje).where(Pasaje.id_reserva == id_reserva))
