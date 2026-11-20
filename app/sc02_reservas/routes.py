from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc02_reservas.schemas import LiberacionResponse, ReservaRequest, ReservaResponse, ReservaMultipleRequest, ReservaMultipleResponse, EstadoReservaResponse
from app.sc02_reservas.service import liberar_reserva, registrar_reserva, registrar_reservas_multiples, consultar_estado_reserva
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Reserva
from sqlalchemy import select


router = APIRouter(prefix="/api/v1", tags=["Reservas"])
errors = {code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 500, 501, 503)}

@router.get("/admin/reservas", operation_id="listarReservasAdministracion")
def listar_reservas_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS"))], estado: str | None = None):
    query = select(Reserva).order_by(Reserva.created_at.desc())
    if estado: query = query.where(Reserva.estado == estado)
    return [{"idReserva": r.id_reserva, "idViaje": r.id_viaje, "idAsiento": r.id_asiento, "estado": r.estado, "dni": r.pasajero_dni, "vencimiento": r.vencimiento} for r in db.scalars(query).all()]

@router.get("/admin/reservas/{id_reserva}", operation_id="consultarReservaAdministracion", responses=errors)
def consultar_reserva_admin(id_reserva: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS"))]):
    r = db.get(Reserva, id_reserva)
    if not r: from app.shared.errors import ApiError; raise ApiError(404, "No encontramos la reserva solicitada.")
    return {"idReserva": r.id_reserva, "idViaje": r.id_viaje, "idAsiento": r.id_asiento, "estado": r.estado, "dni": r.pasajero_dni, "nombres": r.pasajero_nombres, "apellidos": r.pasajero_apellidos, "vencimiento": r.vencimiento}


@router.post("/reservas", status_code=201, operation_id="registrarReserva", response_model=ReservaResponse, responses=errors)
def post_reserva(
    data: ReservaRequest,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("VENTAS"))],
):
    return registrar_reserva(db, data)

@router.post("/reservas/multiples", status_code=201, operation_id="registrarReservasMultiples", response_model=ReservaMultipleResponse, responses=errors)
def post_reservas_multiples(data: ReservaMultipleRequest, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS"))]):
    return registrar_reservas_multiples(db, data)

@router.get("/reservas/{id_reserva}", response_model=EstadoReservaResponse, operation_id="consultarEstadoReserva", responses=errors)
def get_estado_reserva(id_reserva: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS", "ADMIN"))]):
    return consultar_estado_reserva(db, id_reserva)


@router.post("/reservas/{id_reserva}/liberacion", operation_id="liberarAsiento", response_model=LiberacionResponse, responses=errors)
def post_liberacion(
    id_reserva: int,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("VENTAS"))],
):
    return liberar_reserva(db, id_reserva)
