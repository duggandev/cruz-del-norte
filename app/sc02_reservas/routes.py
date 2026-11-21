from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
import jwt
from sqlalchemy.orm import Session

from app.sc02_reservas.schemas import LiberacionResponse, ReservaRequest, ReservaResponse, ReservaMultipleRequest, ReservaMultipleResponse, EstadoReservaResponse, ReservaHoldRequest, PasajeroUpdateRequest
from app.sc02_reservas.service import liberar_reserva, registrar_reserva, registrar_reservas_multiples, consultar_estado_reserva, retener_asiento, actualizar_pasajero
from app.shared.database import SessionLocal, get_db
from app.shared.errors import ErrorResponse
from app.shared.security import Principal, require_roles
from app.shared.models import Reserva
from sqlalchemy import select
from app.shared.models import Viaje
from app.shared.pricing import seat_layout
from app.shared.config import settings
from app.sc02_reservas.realtime import realtime, seat_snapshot


router = APIRouter(prefix="/api/v1", tags=["Reservas"])
errors = {code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 500, 501, 503)}

@router.get("/admin/reservas", operation_id="listarReservasAdministracion")
def listar_reservas_admin(db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS"))], estado: str | None = None):
    query = select(Reserva).order_by(Reserva.created_at.desc())
    if estado: query = query.where(Reserva.estado == estado)
    return [{"idReserva": r.id_reserva, "idViaje": r.id_viaje, "idAsiento": r.id_asiento, "numeroAsiento": seat_layout(r.id_asiento, db.get(Viaje, r.id_viaje).tipo_bus)["numero"], "piso": seat_layout(r.id_asiento, db.get(Viaje, r.id_viaje).tipo_bus)["piso"], "estado": r.estado, "dni": r.pasajero_dni, "vencimiento": r.vencimiento} for r in db.scalars(query).all()]

@router.get("/admin/reservas/{id_reserva}", operation_id="consultarReservaAdministracion", responses=errors)
def consultar_reserva_admin(id_reserva: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("ADMIN", "VENTAS"))]):
    r = db.get(Reserva, id_reserva)
    if not r: from app.shared.errors import ApiError; raise ApiError(404, "No encontramos la reserva solicitada.")
    viaje = db.get(Viaje, r.id_viaje)
    layout = seat_layout(r.id_asiento, viaje.tipo_bus)
    return {"idReserva": r.id_reserva, "idViaje": r.id_viaje, "idAsiento": r.id_asiento, "numeroAsiento": layout["numero"], "piso": layout["piso"], "estado": r.estado, "dni": r.pasajero_dni, "nombres": r.pasajero_nombres, "apellidos": r.pasajero_apellidos, "vencimiento": r.vencimiento}


@router.post("/reservas", status_code=201, operation_id="registrarReserva", response_model=ReservaResponse, responses=errors)
def post_reserva(
    data: ReservaRequest,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("VENTAS"))],
    background_tasks: BackgroundTasks,
):
    body = registrar_reserva(db, data)
    # Se publica solo después del commit realizado por el servicio.
    background_tasks.add_task(realtime.publish, data.id_viaje, {
        "type": "seat_held", "idViaje": data.id_viaje,
        "idAsiento": data.id_asiento, "idReserva": body["idReserva"],
        "estado": body["estado"], "vencimiento": body["vencimiento"],
    })
    return body

@router.post("/reservas/hold", status_code=201, response_model=ReservaResponse, operation_id="retenerAsiento", responses=errors)
def post_hold(data: ReservaHoldRequest, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS"))], background_tasks: BackgroundTasks):
    body = retener_asiento(db, data)
    background_tasks.add_task(realtime.publish, data.id_viaje, {"type": "seat_held", "idViaje": data.id_viaje, "idAsiento": data.id_asiento, "idReserva": body["idReserva"], "estado": body["estado"], "vencimiento": body["vencimiento"]})
    return body

@router.patch("/reservas/{id_reserva}/pasajero", operation_id="actualizarPasajeroReserva", responses=errors)
def patch_pasajero(id_reserva: int, data: PasajeroUpdateRequest, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS"))]):
    return actualizar_pasajero(db, id_reserva, data)

@router.post("/reservas/multiples", status_code=201, operation_id="registrarReservasMultiples", response_model=ReservaMultipleResponse, responses=errors)
def post_reservas_multiples(data: ReservaMultipleRequest, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS"))], background_tasks: BackgroundTasks):
    body = registrar_reservas_multiples(db, data)
    for reservation in body["reservas"]:
        background_tasks.add_task(realtime.publish, data.id_viaje, {
            "type": "seat_held", "idViaje": data.id_viaje,
            "idAsiento": reservation["idAsiento"], "idReserva": reservation["idReserva"],
            "estado": reservation["estado"], "vencimiento": reservation["vencimiento"],
        })
    return body

@router.get("/reservas/{id_reserva}", response_model=EstadoReservaResponse, operation_id="consultarEstadoReserva", responses=errors)
def get_estado_reserva(id_reserva: int, db: Annotated[Session, Depends(get_db)], _principal: Annotated[Principal, Depends(require_roles("VENTAS", "ADMIN"))]):
    return consultar_estado_reserva(db, id_reserva)


@router.post("/reservas/{id_reserva}/liberacion", operation_id="liberarAsiento", response_model=LiberacionResponse, responses=errors)
def post_liberacion(
    id_reserva: int,
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[Principal, Depends(require_roles("VENTAS"))],
    background_tasks: BackgroundTasks,
):
    reserva = db.get(Reserva, id_reserva)
    if not reserva:
        from app.shared.errors import ApiError
        raise ApiError(404, "No encontramos la reserva solicitada.")
    trip_id = reserva.id_viaje
    body = liberar_reserva(db, id_reserva)
    background_tasks.add_task(realtime.publish, trip_id, {
        "type": "seat_released", "idViaje": trip_id,
        "idAsiento": reserva.id_asiento, "idReserva": id_reserva,
        "estado": body["estado"],
    })
    return body


def _websocket_principal(websocket: WebSocket):
    token = websocket.query_params.get("access_token")
    authorization = websocket.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        roles = payload.get("roles", [])
        if not payload.get("sub") or not isinstance(roles, list):
            return None
        if "ADMIN" not in roles and "VENTAS" not in roles:
            return None
        return payload
    except jwt.InvalidTokenError:
        return None


@router.websocket("/reservas/ws/{id_viaje}")
async def reservas_websocket(websocket: WebSocket, id_viaje: int):
    """Emite el mapa inicial y cambios de asientos confirmados en tiempo real.

    En navegador se puede conectar con:
    ``wss://dominio/api/v1/reservas/ws/123?access_token=JWT``.
    """
    if _websocket_principal(websocket) is None:
        await websocket.close(code=1008, reason="Token inválido o sin permisos")
        return
    db = SessionLocal()
    try:
        snapshot = seat_snapshot(db, id_viaje)
        if snapshot.get("type") == "error":
            await websocket.close(code=1008, reason=snapshot["message"])
            return
        await realtime.connect(id_viaje, websocket)
        await websocket.send_json(snapshot)
        while True:
            # El cliente puede enviar ping; recibir mantiene viva la conexión.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await realtime.disconnect(id_viaje, websocket)
        db.close()
