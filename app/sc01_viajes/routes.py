from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.sc01_viajes.schemas import DisponibilidadResponse
from app.sc01_viajes.service import consultar_disponibilidad
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Viaje, AsientoViaje, Reserva
from sqlalchemy import select
from app.sc02_reservas.service import tipo_asiento
from app.shared.pricing import seat_fare_centavos, seat_layout


router = APIRouter(prefix="/api/v1", tags=["Disponibilidad de viajes"])

@router.get("/viajes/{id_viaje}/asientos", operation_id="consultarMapaAsientos")
def get_mapa_asientos(id_viaje: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS", "EMISION", "MANTENIMIENTO"))]):
    viaje = db.get(Viaje, id_viaje)
    if not viaje:
        from app.shared.errors import ApiError
        raise ApiError(404, "No encontramos el viaje solicitado.")
    ahora = datetime.now(ZoneInfo("America/Lima")).replace(tzinfo=None)
    reservas = db.scalars(select(Reserva).where(Reserva.id_viaje == id_viaje, Reserva.estado.in_(("TEMPORAL", "CONFIRMADA")))).all()
    bloqueos = {}
    for r in reservas:
        vencimiento = r.vencimiento.replace(tzinfo=None) if r.vencimiento.tzinfo else r.vencimiento
        if r.estado == "CONFIRMADA" or vencimiento > ahora:
            bloqueos[r.id_asiento] = r
    asientos = []
    for a in db.scalars(select(AsientoViaje).where(AsientoViaje.id_viaje == id_viaje).order_by(AsientoViaje.id_asiento)).all():
        bloqueo = bloqueos.get(a.id_asiento)
        layout = seat_layout(a.id_asiento, viaje.tipo_bus)
        asientos.append({"idAsiento": a.id_asiento, "tipo": tipo_asiento(a.id_asiento), "piso": layout["piso"], "fila": layout["fila"], "columna": layout["columna"], "individual": layout["individual"], "precio": seat_fare_centavos(viaje.tarifa_centavos, a.id_asiento, viaje.tipo_bus) / 100, "estado": "RESERVADO" if bloqueo else a.estado, "disponible": bloqueo is None and a.estado == "DISPONIBLE", "idReserva": bloqueo.id_reserva if bloqueo else None})
    return {"idViaje": id_viaje, "tipoBus": viaje.tipo_bus, "pisos": viaje.pisos, "capacidad": viaje.capacidad, "orientacionMapa": "HORIZONTAL", "frente": "DELANTERA", "indicadorFrente": "TIMON", "tarifaBase": viaje.tarifa_centavos / 100, "asientos": asientos}

@router.get("/admin/viajes", operation_id="listarViajesAdministracion")
def listar_viajes_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "MANTENIMIENTO"))], estado: str | None = None, fecha: date | None = None):
    query = select(Viaje).order_by(Viaje.fecha, Viaje.hora_salida)
    if estado: query = query.where(Viaje.estado == estado)
    if fecha: query = query.where(Viaje.fecha == fecha)
    return [{"idViaje": v.id_viaje, "origen": v.origen, "destino": v.destino, "fecha": v.fecha, "horaSalida": v.hora_salida, "tarifa": v.tarifa_centavos / 100, "estado": v.estado, "tipoBus": v.tipo_bus, "pisos": v.pisos, "capacidad": v.capacidad} for v in db.scalars(query).all()]


@router.get(
    "/viajes/disponibilidad",
    operation_id="consultarDisponibilidad",
    response_model=DisponibilidadResponse,
    responses={203: {"model": DisponibilidadResponse}, 204: {"description": "No existen viajes"}, **{code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 405, 406, 429, 500, 503)}},
)
def get_disponibilidad(
    origen: Annotated[str, Query(min_length=1, max_length=120)],
    destino: Annotated[str, Query(min_length=1, max_length=120)],
    fecha: date,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("VENTAS", "EMISION", "MANTENIMIENTO"))],
):
    result = consultar_disponibilidad(db, origen, destino, fecha)
    return result if result is not None else Response(status_code=204)
