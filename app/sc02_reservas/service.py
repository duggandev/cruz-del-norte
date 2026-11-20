from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.sc02_reservas import repository
from app.sc02_reservas.schemas import ReservaRequest, ReservaMultipleRequest
from app.shared.config import settings
from app.shared.errors import ApiError
from app.shared.models import Reserva


LIMA = ZoneInfo("America/Lima")


def _local_naive(value: datetime) -> datetime:
    return value.astimezone(LIMA).replace(tzinfo=None)


def registrar_reserva(db: Session, data: ReservaRequest) -> dict:
    if data.pasajero.fecha_nacimiento:
        hoy = date.today()
        edad = hoy.year - data.pasajero.fecha_nacimiento.year - ((hoy.month, hoy.day) < (data.pasajero.fecha_nacimiento.month, data.pasajero.fecha_nacimiento.day))
        if edad < 0 or edad > 120:
            raise ApiError(422, "La fecha de nacimiento no es valida.")
        if edad < 12 and (data.pasajero.viaja_solo or not data.pasajero.acompanante_mayor_edad):
            raise ApiError(422, "Los menores de 12 anos no pueden viajar solos y requieren un adulto autorizado.")
        if edad < 18 and not data.pasajero.permiso_notarial:
            raise ApiError(422, "Los menores que viajan sin sus padres requieren permiso notarial vigente.")
    if data.id_canal == 4:
        raise ApiError(501, "Las plataformas externas todavía no están implementadas.")
    if not data.pasajero.dni.isdigit() or len(data.pasajero.dni) != 8:
        raise ApiError(422, "El DNI del pasajero debe contener exactamente ocho números.")
    try:
        db.execute(text("BEGIN IMMEDIATE" if db.bind.dialect.name == "sqlite" else "BEGIN"))
        now = datetime.now(LIMA)
        repository.expirar_reservas(db, _local_naive(now))
        viaje = repository.get_viaje(db, data.id_viaje)
        if not viaje:
            raise ApiError(404, "No encontramos el viaje solicitado.")
        if viaje.estado not in {"PROGRAMADO", "DISPONIBLE"}:
            raise ApiError(409, "El viaje no admite nuevas reservas.")
        asiento = repository.get_asiento(db, data.id_viaje, data.id_asiento)
        if not asiento:
            raise ApiError(404, "El asiento no existe para el viaje indicado.")
        if asiento.estado != "DISPONIBLE":
            raise ApiError(409, "El asiento no está disponible.")
        if repository.get_bloqueo(db, data.id_viaje, data.id_asiento):
            raise ApiError(409, "El asiento ya se encuentra reservado.")
        expiration = now + timedelta(minutes=settings.reservation_ttl_minutes)
        reserva = Reserva(
            id_viaje=data.id_viaje,
            id_asiento=data.id_asiento,
            id_canal=data.id_canal,
            pasajero_dni=data.pasajero.dni,
            pasajero_nombres=data.pasajero.nombres.strip(),
            pasajero_apellidos=data.pasajero.apellidos.strip(),
            estado="TEMPORAL",
            vencimiento=_local_naive(expiration),
        )
        if not reserva.pasajero_nombres or not reserva.pasajero_apellidos:
            raise ApiError(422, "Nombres y apellidos son obligatorios.")
        db.add(reserva)
        db.flush()
        body = {
            "idReserva": reserva.id_reserva,
            "idViaje": reserva.id_viaje,
            "idAsiento": reserva.id_asiento,
            "estado": reserva.estado,
            "vencimiento": expiration.isoformat(),
        }
        db.commit()
        return body
    except ApiError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "El asiento fue reservado por otra solicitud.") from exc
    except OperationalError as exc:
        db.rollback()
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc


def registrar_reservas_multiples(db: Session, data: ReservaMultipleRequest) -> dict:
    asientos = [item.id_asiento for item in data.pasajeros]
    if len(set(asientos)) != len(asientos):
        raise ApiError(422, "No se puede repetir un asiento en la misma compra.")
    reservas = []
    for item in data.pasajeros:
        reservas.append(registrar_reserva(db, ReservaRequest(idViaje=data.id_viaje, idAsiento=item.id_asiento, idCanal=data.id_canal, pasajero=item.pasajero)))
    return {"reservas": reservas, "cantidad": len(reservas)}


def liberar_reserva(db: Session, id_reserva: int) -> dict:
    try:
        db.execute(text("BEGIN IMMEDIATE" if db.bind.dialect.name == "sqlite" else "BEGIN"))
        now = datetime.now(LIMA)
        repository.expirar_reservas(db, _local_naive(now))
        reserva = repository.get_reserva(db, id_reserva)
        if not reserva:
            raise ApiError(404, "No encontramos la reserva solicitada.")
        if repository.tiene_pago_aprobado(db, id_reserva):
            raise ApiError(409, "No se puede liberar una reserva con pago aprobado.")
        if reserva.estado == "CONFIRMADA":
            raise ApiError(409, "No se puede liberar una reserva confirmada.")
        if reserva.estado == "TEMPORAL":
            reserva.estado = "CANCELADA"
        db.commit()
        return {"idReserva": reserva.id_reserva, "estado": reserva.estado}
    except ApiError:
        db.rollback()
        raise
    except OperationalError as exc:
        db.rollback()
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc
