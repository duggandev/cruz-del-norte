from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.models import ProgramacionMantenimiento, Vehiculo


def get_vehiculo(db: Session, id_vehiculo: int) -> Vehiculo | None:
    return db.get(Vehiculo, id_vehiculo)


def get_programacion_activa(db: Session, id_vehiculo: int, fecha):
    return db.scalar(
        select(ProgramacionMantenimiento).where(
            ProgramacionMantenimiento.id_vehiculo == id_vehiculo,
            ProgramacionMantenimiento.fecha == fecha,
            ProgramacionMantenimiento.estado == "PROGRAMADO",
        )
    )
