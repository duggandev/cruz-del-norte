from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc06_mantenimiento.schemas import ProgramacionRequest, ProgramacionResponse
from app.sc06_mantenimiento.service import programar
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles


router = APIRouter(prefix="/api/v1", tags=["Mantenimiento"])


@router.post(
    "/programaciones", status_code=201, operation_id="programarMantenimiento", response_model=ProgramacionResponse,
    responses={code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 500, 503)},
)
def post_programacion(
    data: ProgramacionRequest,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("MANTENIMIENTO"))],
):
    return programar(db, data)
