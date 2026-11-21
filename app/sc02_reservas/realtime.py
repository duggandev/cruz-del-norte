"""Canal de disponibilidad en tiempo real para los mapas de asientos.

La base de datos sigue siendo la fuente de verdad. Este módulo únicamente
distribuye cambios ya confirmados por PostgreSQL a los clientes conectados.
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.config import settings
from app.shared.models import AsientoViaje, Reserva, Viaje
from app.shared.pricing import seat_layout
from app.sc02_reservas.service import tipo_asiento


class SeatRealtime:
    def __init__(self) -> None:
        self._clients: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, trip_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients[trip_id].add(websocket)

    async def disconnect(self, trip_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            clients = self._clients.get(trip_id)
            if clients:
                clients.discard(websocket)
                if not clients:
                    self._clients.pop(trip_id, None)

    async def publish(self, trip_id: int, event: dict) -> None:
        async with self._lock:
            clients = list(self._clients.get(trip_id, ()))
        stale: list[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_json(event)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            await self.disconnect(trip_id, websocket)


realtime = SeatRealtime()


def seat_snapshot(db: Session, trip_id: int) -> dict:
    viaje = db.get(Viaje, trip_id)
    if not viaje:
        return {"type": "error", "code": 404, "message": "Viaje no encontrado."}
    active = {
        reserva.id_asiento: reserva
        for reserva in db.scalars(
            select(Reserva).where(
                Reserva.id_viaje == trip_id,
                Reserva.estado.in_(("TEMPORAL", "CONFIRMADA")),
            )
        ).all()
    }
    seats = []
    now = datetime.now(timezone.utc)
    for seat in db.scalars(
        select(AsientoViaje).where(AsientoViaje.id_viaje == trip_id).order_by(AsientoViaje.id_asiento)
    ).all():
        reservation = active.get(seat.id_asiento)
        layout = seat_layout(seat.id_asiento, viaje.tipo_bus)
        expires = None
        if reservation and reservation.vencimiento:
            expires = reservation.vencimiento.replace(tzinfo=timezone.utc).isoformat()
        seats.append({
            "idAsiento": seat.id_asiento,
            "numero": layout["numero"],
            "tipo": tipo_asiento(seat.id_asiento),
            "piso": layout["piso"],
            "estado": reservation.estado if reservation else seat.estado,
            "disponible": reservation is None and seat.estado == "DISPONIBLE",
            "idReserva": reservation.id_reserva if reservation else None,
            "vencimiento": expires,
        })
    return {"type": "snapshot", "idViaje": trip_id, "servidorAhora": now.isoformat(), "asientos": seats}
