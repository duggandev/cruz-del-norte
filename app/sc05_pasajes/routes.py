from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc05_pasajes.schemas import PasajeRequest, PasajeResponse
from app.sc05_pasajes.service import emitir_pasaje
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Pasaje, Pago, Reserva, Viaje
from sqlalchemy import select, func
from datetime import date


router = APIRouter(prefix="/api/v1", tags=["Pasajes"])

@router.get("/admin/pasajes", operation_id="listarPasajesAdministracion")
def listar_pasajes_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS", "EMISION"))], estado: str | None = None):
    query = select(Pasaje).order_by(Pasaje.fecha_emision.desc())
    if estado: query = query.where(Pasaje.estado == estado)
    return [{"codigo": p.codigo, "idReserva": p.id_reserva, "estado": p.estado, "fechaEmision": p.fecha_emision, "documentoUrl": p.documento_url} for p in db.scalars(query).all()]

@router.get("/admin/ventas", operation_id="consultarHistorialVentas")
def historial_ventas(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS", "EMISION"))], desde: date | None = None, hasta: date | None = None):
    query = select(Pasaje, Reserva, Viaje, Pago).join(Reserva, Pasaje.id_reserva == Reserva.id_reserva).join(Viaje, Reserva.id_viaje == Viaje.id_viaje).join(Pago, Pasaje.id_pago == Pago.id_pago).where(Pasaje.estado == "EMITIDO").order_by(Pasaje.fecha_emision.desc())
    if desde: query = query.where(func.date(Pasaje.fecha_emision) >= desde.isoformat())
    if hasta: query = query.where(func.date(Pasaje.fecha_emision) <= hasta.isoformat())
    rows = db.execute(query).all()
    ventas = [{"codigo": p.codigo, "codigoPago": pago.id_transaccion, "idReserva": r.id_reserva, "dni": r.pasajero_dni, "pasajero": f"{r.pasajero_nombres} {r.pasajero_apellidos}", "origen": v.origen, "destino": v.destino, "fechaViaje": v.fecha, "asiento": r.id_asiento, "monto": pago.importe_centavos / 100, "importe": pago.importe_centavos / 100, "medioPago": pago.medio_pago, "fechaEmision": p.fecha_emision, "documentoUrl": p.documento_url} for p, r, v, pago in rows]
    return {"desde": desde, "hasta": hasta, "cantidad": len(ventas), "total": round(sum(item["importe"] for item in ventas), 2), "ventas": ventas}


@router.post(
    "/pasajes", status_code=201, operation_id="emitirPasaje", response_model=PasajeResponse,
    responses={code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 500, 503)},
)
def post_pasaje(
    data: PasajeRequest,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("EMISION"))],
):
    body, _path = emitir_pasaje(db, data)
    return body
