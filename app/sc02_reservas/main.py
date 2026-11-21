import asyncio
from contextlib import suppress
from datetime import datetime, timezone

from sqlalchemy import select

from app.sc02_reservas.routes import router
from app.shared.app_factory import create_app
from app.shared.database import SessionLocal
from app.shared.models import Reserva
from app.sc02_reservas.realtime import realtime

app = create_app("SC-02 Gestión Reservas")
app.include_router(router)


async def _expire_reservations() -> None:
    while True:
        await asyncio.sleep(15)
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            expired = db.scalars(select(Reserva).where(Reserva.estado == "TEMPORAL", Reserva.vencimiento <= now)).all()
            if not expired:
                continue
            for reservation in expired:
                reservation.estado = "VENCIDA"
            db.commit()
            for reservation in expired:
                await realtime.publish(reservation.id_viaje, {
                    "type": "seat_released", "idViaje": reservation.id_viaje,
                    "idAsiento": reservation.id_asiento, "idReserva": reservation.id_reserva,
                    "estado": "VENCIDA",
                })
        finally:
            db.close()


@app.on_event("startup")
async def start_expiration_worker() -> None:
    app.state.expiration_task = asyncio.create_task(_expire_reservations())


@app.on_event("shutdown")
async def stop_expiration_worker() -> None:
    task = getattr(app.state, "expiration_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
