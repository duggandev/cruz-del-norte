from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.sc02_reservas import repository
from app.sc02_reservas.schemas import ReservaRequest, ReservaMultipleRequest, ReservaHoldRequest, PasajeroUpdateRequest
from app.shared.config import settings
from app.shared.errors import ApiError
from app.shared.models import Reserva, Viaje
from app.shared.pricing import seat_layout


LIMA = ZoneInfo("America/Lima")

def tipo_asiento(id_asiento: int) -> str:
    if id_asiento <= 4: return "VIP"
    if id_asiento <= 12: return "PREFERENCIAL"
    return "ESTANDAR"


def _local_naive(value: datetime) -> datetime:
    return value.astimezone(LIMA).replace(tzinfo=None)

def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)

def _db_expiration(db: Session, value: datetime) -> datetime:
    return _utc_naive(value) if db.bind.dialect.name == "sqlite" else value


def registrar_reserva(db: Session, data: ReservaRequest) -> dict:
    if data.tipo_asiento and data.tipo_asiento != tipo_asiento(data.id_asiento):
        raise ApiError(422, f"El asiento {data.id_asiento} pertenece a la categoria {tipo_asiento(data.id_asiento)}.")
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
        now = datetime.now(timezone.utc)
        repository.expirar_reservas(db, _utc_naive(now))
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
            vencimiento=_db_expiration(db, expiration),
        )
        if not reserva.pasajero_nombres or not reserva.pasajero_apellidos:
            raise ApiError(422, "Nombres y apellidos son obligatorios.")
        db.add(reserva)
        db.flush()
        body = {
            "idReserva": reserva.id_reserva,
            "idViaje": reserva.id_viaje,
            "idAsiento": reserva.id_asiento,
            "numeroAsiento": seat_layout(reserva.id_asiento, viaje.tipo_bus)["numero"],
            "piso": seat_layout(reserva.id_asiento, viaje.tipo_bus)["piso"],
            "estado": reserva.estado,
            "vencimiento": expiration.isoformat(),
            "minutosRestantes": settings.reservation_ttl_minutes,
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


def retener_asiento(db: Session, data: ReservaHoldRequest) -> dict:
    """Bloquea el asiento inmediatamente al seleccionarlo en el mapa."""
    try:
        db.execute(text("BEGIN IMMEDIATE" if db.bind.dialect.name == "sqlite" else "BEGIN"))
        now = datetime.now(timezone.utc)
        repository.expirar_reservas(db, _utc_naive(now))
        viaje = repository.get_viaje(db, data.id_viaje)
        if not viaje:
            raise ApiError(404, "No encontramos el viaje solicitado.")
        asiento = repository.get_asiento(db, data.id_viaje, data.id_asiento)
        if not asiento:
            raise ApiError(404, "El asiento no existe para el viaje indicado.")
        if asiento.estado != "DISPONIBLE" or repository.get_bloqueo(db, data.id_viaje, data.id_asiento):
            raise ApiError(409, "El asiento ya no está disponible.")
        expiration = now + timedelta(minutes=settings.reservation_ttl_minutes)
        reserva = Reserva(id_viaje=data.id_viaje, id_asiento=data.id_asiento, id_canal=data.id_canal,
                          pasajero_dni=f"HOLD-{data.id_viaje}-{data.id_asiento}-{int(now.timestamp())}",
                          pasajero_nombres="Pendiente", pasajero_apellidos="Pendiente", estado="TEMPORAL",
                          vencimiento=_db_expiration(db, expiration))
        db.add(reserva); db.flush()
        body = {"idReserva": reserva.id_reserva, "idViaje": reserva.id_viaje, "idAsiento": reserva.id_asiento,
                "numeroAsiento": seat_layout(reserva.id_asiento, viaje.tipo_bus)["numero"], "piso": seat_layout(reserva.id_asiento, viaje.tipo_bus)["piso"],
                "estado": reserva.estado, "vencimiento": expiration.isoformat(), "minutosRestantes": settings.reservation_ttl_minutes}
        db.commit()
        return body
    except ApiError:
        db.rollback(); raise
    except IntegrityError as exc:
        db.rollback(); raise ApiError(409, "El asiento fue reservado por otra solicitud.") from exc


def actualizar_pasajero(db: Session, id_reserva: int, data: PasajeroUpdateRequest) -> dict:
    if not data.dni.isdigit() or len(data.dni) != 8:
        raise ApiError(422, "El DNI del pasajero debe contener exactamente ocho números.")
    reserva = repository.get_reserva(db, id_reserva)
    if not reserva:
        raise ApiError(404, "No encontramos la reserva solicitada.")
    if reserva.estado != "TEMPORAL":
        raise ApiError(409, "La reserva ya no admite datos de pasajero.")
    reserva.pasajero_dni, reserva.pasajero_nombres, reserva.pasajero_apellidos = data.dni, data.nombres.strip(), data.apellidos.strip()
    if not reserva.pasajero_nombres or not reserva.pasajero_apellidos:
        raise ApiError(422, "Nombres y apellidos son obligatorios.")
    db.commit()
    return {"idReserva": reserva.id_reserva, "estado": reserva.estado}


def registrar_reservas_multiples(db: Session, data: ReservaMultipleRequest) -> dict:
    asientos = [item.id_asiento for item in data.pasajeros]
    if len(set(asientos)) != len(asientos):
        raise ApiError(422, "No se puede repetir un asiento en la misma compra.")
    reservas = []
    for item in data.pasajeros:
        reservas.append(registrar_reserva(db, ReservaRequest(idViaje=data.id_viaje, idAsiento=item.id_asiento, idCanal=data.id_canal, pasajero=item.pasajero, tipoAsiento=item.tipo_asiento)))
    return {"reservas": reservas, "cantidad": len(reservas)}


def consultar_estado_reserva(db: Session, id_reserva: int) -> dict:
    row = db.execute(select(Reserva, Viaje).join(Viaje, Reserva.id_viaje == Viaje.id_viaje).where(Reserva.id_reserva == id_reserva)).one_or_none()
    if not row:
        raise ApiError(404, "No encontramos la reserva solicitada.")
    reserva, viaje = row
    now = datetime.now(timezone.utc)
    vencimiento = reserva.vencimiento.replace(tzinfo=timezone.utc) if reserva.vencimiento.tzinfo is None else reserva.vencimiento.astimezone(timezone.utc)
    minutos = max(0.0, (vencimiento - now).total_seconds() / 60)
    if minutos <= 0 and reserva.estado == "TEMPORAL":
        reserva.estado = "VENCIDA"
        db.commit()
    layout = seat_layout(reserva.id_asiento, viaje.tipo_bus)
    return {"idReserva": reserva.id_reserva, "idViaje": reserva.id_viaje, "idAsiento": reserva.id_asiento, "numeroAsiento": layout["numero"], "piso": layout["piso"], "estado": reserva.estado, "vencimiento": vencimiento.isoformat(), "minutosRestantes": round(minutos, 2), "puedePagar": reserva.estado == "TEMPORAL" and minutos > 0}


def liberar_reserva(db: Session, id_reserva: int) -> dict:
    try:
        db.execute(text("BEGIN IMMEDIATE" if db.bind.dialect.name == "sqlite" else "BEGIN"))
        now = datetime.now(timezone.utc)
        repository.expirar_reservas(db, _utc_naive(now))
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
