from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.sc01_viajes.schemas import DisponibilidadResponse
from app.sc01_viajes.service import consultar_disponibilidad
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Viaje
from sqlalchemy import select


router = APIRouter(prefix="/api/v1", tags=["Disponibilidad de viajes"])

@router.get("/admin/viajes", operation_id="listarViajesAdministracion")
def listar_viajes_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "MANTENIMIENTO"))], estado: str | None = None, fecha: date | None = None):
    query = select(Viaje).order_by(Viaje.fecha, Viaje.hora_salida)
    if estado: query = query.where(Viaje.estado == estado)
    if fecha: query = query.where(Viaje.fecha == fecha)
    return [{"idViaje": v.id_viaje, "origen": v.origen, "destino": v.destino, "fecha": v.fecha, "horaSalida": v.hora_salida, "tarifa": v.tarifa_centavos / 100, "estado": v.estado} for v in db.scalars(query).all()]


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
