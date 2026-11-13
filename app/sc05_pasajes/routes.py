from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.sc05_pasajes.schemas import PasajeRequest, PasajeResponse
from app.sc05_pasajes.service import emitir_pasaje
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles


router = APIRouter(prefix="/api/v1", tags=["Pasajes"])


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
