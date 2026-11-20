from typing import Annotated
from fastapi import APIRouter, Depends, Response
from app.sc03_pasajeros.schemas import ValidacionPasajeroRequest, ValidacionPasajeroResponse
from app.sc03_pasajeros.service import validar_pasajero, politicas_viaje
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Reserva
from app.shared.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["Validacion de pasajeros"])

@router.get("/pasajeros/politicas", operation_id="consultarPoliticasPasajeros")
def get_politicas():
    return politicas_viaje()

@router.get("/admin/pasajeros", operation_id="listarPasajerosAdministracion")
def listar_pasajeros_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "CAJA"))], dni: str | None = None):
    query = select(Reserva.pasajero_dni, Reserva.pasajero_nombres, Reserva.pasajero_apellidos).distinct()
    if dni: query = query.where(Reserva.pasajero_dni == dni)
    return [{"dni": row[0], "nombres": row[1], "apellidos": row[2]} for row in db.execute(query).all()]

@router.post("/pasajeros/validaciones", operation_id="validarPasajero", response_model=ValidacionPasajeroResponse, responses={203: {"model": ValidacionPasajeroResponse}, **{code: {"model": ErrorResponse} for code in (400, 401, 403, 406, 429, 500, 503)}})
def post_validacion(data: ValidacionPasajeroRequest, response: Response, _principal: Annotated[Principal, Depends(require_roles("CAJA", "EMISION", "MANTENIMIENTO"))]):
    body, status = validar_pasajero(data)
    response.status_code = status
    return body
