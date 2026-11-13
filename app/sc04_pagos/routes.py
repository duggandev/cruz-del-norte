from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.sc04_pagos.schemas import PagoRequest, PagoResponse
from app.sc04_pagos.service import procesar_pago
from app.shared.database import get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles


router = APIRouter(prefix="/api/v1", tags=["Pagos"])


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
