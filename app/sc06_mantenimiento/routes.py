from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc06_mantenimiento.schemas import ProgramacionRequest, ProgramacionResponse
from app.sc06_mantenimiento.service import programar
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import ProgramacionMantenimiento
from sqlalchemy import select


router = APIRouter(prefix="/api/v1", tags=["Mantenimiento"])

@router.get("/admin/programaciones", operation_id="listarMantenimientosAdministracion")
def listar_programaciones_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "MANTENIMIENTO"))], estado: str | None = None):
    query = select(ProgramacionMantenimiento).order_by(ProgramacionMantenimiento.fecha)
    if estado: query = query.where(ProgramacionMantenimiento.estado == estado)
    return [{"idProgramacion": p.id_programacion, "codigo": p.codigo, "idVehiculo": p.id_vehiculo, "kilometraje": p.kilometraje, "fecha": p.fecha, "tipo": p.tipo, "estado": p.estado} for p in db.scalars(query).all()]


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
