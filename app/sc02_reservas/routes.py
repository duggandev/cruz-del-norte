from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc02_reservas.schemas import LiberacionResponse, ReservaRequest, ReservaResponse
from app.sc02_reservas.service import liberar_reserva, registrar_reserva
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles


router = APIRouter(prefix="/api/v1", tags=["Reservas"])
errors = {code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 500, 501, 503)}


@router.post("/reservas", status_code=201, operation_id="registrarReserva", response_model=ReservaResponse, responses=errors)
def post_reserva(
    data: ReservaRequest,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("CAJA"))],
):
    return registrar_reserva(db, data)


@router.post("/reservas/{id_reserva}/liberacion", operation_id="liberarAsiento", response_model=LiberacionResponse, responses=errors)
def post_liberacion(
    id_reserva: int,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("CAJA"))],
):
    return liberar_reserva(db, id_reserva)
