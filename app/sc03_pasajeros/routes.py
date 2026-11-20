from typing import Annotated
from fastapi import APIRouter, Depends, Response
from app.sc03_pasajeros.schemas import ValidacionPasajeroRequest, ValidacionPasajeroResponse
from app.sc03_pasajeros.service import validar_pasajero, politicas_viaje
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Reserva, Pasaje
from app.shared.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["Validacion de pasajeros"])

@router.get("/pasajeros/politicas", operation_id="consultarPoliticasPasajeros")
def get_politicas():
    return politicas_viaje()

@router.get("/admin/pasajeros", operation_id="listarPasajerosAdministracion")
def listar_pasajeros_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS"))], dni: str | None = None):
    query = select(Reserva, Pasaje).outerjoin(Pasaje, Pasaje.id_reserva == Reserva.id_reserva).order_by(Reserva.created_at.desc())
    if dni: query = query.where(Reserva.pasajero_dni == dni)
    seen: set[str] = set()
    pasajeros = []
    for reserva, pasaje in db.execute(query).all():
        if reserva.pasajero_dni in seen:
            continue
        seen.add(reserva.pasajero_dni)
        pasajeros.append({"id": reserva.id_reserva, "dni": reserva.pasajero_dni, "nombres": reserva.pasajero_nombres, "apellidos": reserva.pasajero_apellidos, "nombreCompleto": f"{reserva.pasajero_nombres} {reserva.pasajero_apellidos}", "estado": reserva.estado, "tienePasaje": pasaje is not None, "codigo": pasaje.codigo if pasaje else None, "idPasaje": pasaje.id_pasaje if pasaje else None})
    return pasajeros

@router.post("/pasajeros/validaciones", operation_id="validarPasajero", response_model=ValidacionPasajeroResponse, responses={203: {"model": ValidacionPasajeroResponse}, **{code: {"model": ErrorResponse} for code in (400, 401, 403, 406, 429, 500, 503)}})
def post_validacion(data: ValidacionPasajeroRequest, response: Response, _principal: Annotated[Principal, Depends(require_roles("VENTAS", "EMISION", "MANTENIMIENTO"))]):
    body, status = validar_pasajero(data)
    response.status_code = status
    return body
