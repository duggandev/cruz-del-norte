from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.sc04_pagos.schemas import PagoRequest, PagoResponse
from app.sc04_pagos.service import procesar_pago
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Reserva, Viaje, Pago
from sqlalchemy import select
from datetime import datetime, time
from zoneinfo import ZoneInfo


router = APIRouter(prefix="/api/v1", tags=["Pagos"])

@router.get("/admin/pagos", operation_id="listarPagosAdministracion")
def listar_pagos_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "CAJA"))], estado: str | None = None):
    query = select(Pago).order_by(Pago.created_at.desc())
    if estado: query = query.where(Pago.estado == estado)
    return [{"idTransaccion": p.id_transaccion, "idReserva": p.id_reserva, "importe": p.importe_centavos / 100, "medioPago": p.medio_pago, "estado": p.estado, "createdAt": p.created_at} for p in db.scalars(query).all()]

@router.get("/pagos/{id_reserva}/reembolso", operation_id="cotizarReembolso", responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def get_reembolso(id_reserva: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("CAJA"))]):
    row = db.execute(select(Reserva, Viaje).join(Viaje, Reserva.id_viaje == Viaje.id_viaje).where(Reserva.id_reserva == id_reserva)).one_or_none()
    if not row:
        from app.shared.errors import ApiError
        raise ApiError(404, "No encontramos la reserva solicitada.")
    reserva, viaje = row
    salida = datetime.combine(viaje.fecha, time.fromisoformat(viaje.hora_salida), tzinfo=ZoneInfo("America/Lima"))
    horas = (salida - datetime.now(ZoneInfo("America/Lima"))).total_seconds() / 3600
    elegible = horas >= 12 and reserva.estado not in {"CANCELADA", "VENCIDA"}
    return {"idReserva": id_reserva, "elegible": elegible, "horasAntesSalida": round(max(horas, 0), 2), "penalidadPorcentaje": 0 if elegible else None, "mensaje": "Reembolso disponible hasta 12 horas antes para tarifa Regular." if elegible else "Fuera de plazo o reserva no reembolsable."}


@router.post(
    "/pagos", status_code=201, operation_id="procesarPago", response_model=PagoResponse,
    responses={202: {"model": PagoResponse}, **{code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 410, 422, 429, 500, 501, 502, 503, 504)}},
)
def post_pago(
    data: PagoRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("CAJA"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    body, status_code = procesar_pago(db, data, idempotency_key or "")
    response.status_code = status_code
    return body
