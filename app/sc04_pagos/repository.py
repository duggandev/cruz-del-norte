from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.shared.models import IdempotenciaPago, Pago, Reserva, Viaje


def get_reserva_con_viaje(db: Session, id_reserva: int):
    return db.execute(
        select(Reserva, Viaje).join(Viaje, Reserva.id_viaje == Viaje.id_viaje).where(Reserva.id_reserva == id_reserva)
    ).one_or_none()


def get_idempotencia(db: Session, key: str) -> IdempotenciaPago | None:
    return db.get(IdempotenciaPago, key)


def get_pago_aprobado(db: Session, id_reserva: int) -> Pago | None:
    return db.scalar(select(Pago).where(Pago.id_reserva == id_reserva, Pago.estado == "APROBADO"))


def get_next_mock_sequence(db: Session) -> int:
    return int(db.scalar(text(
        "SELECT COALESCE(MAX(CAST(SUBSTR(id_transaccion, 6) AS INTEGER)), 0) + 1 "
        "FROM pagos WHERE id_transaccion LIKE 'MOCK-%'"
    )))
