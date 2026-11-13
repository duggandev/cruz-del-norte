import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.sc06_mantenimiento import repository
from app.sc06_mantenimiento.schemas import ProgramacionRequest
from app.shared.errors import ApiError
from app.shared.models import ProgramacionMantenimiento


LIMA = ZoneInfo("America/Lima")


def programar(db: Session, data: ProgramacionRequest) -> dict:
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        if not repository.get_vehiculo(db, data.id_vehiculo):
            raise ApiError(404, "No encontramos el vehículo solicitado.")
        if data.fecha < datetime.now(LIMA).date():
            raise ApiError(422, "La fecha de programación no puede estar en el pasado.")
        if repository.get_programacion_activa(db, data.id_vehiculo, data.fecha):
            raise ApiError(409, "El vehículo ya tiene una programación activa en esa fecha.")
        for _ in range(10):
            codigo = f"PRG-{secrets.randbelow(10_000):04d}"
            if not db.scalar(text("SELECT 1 FROM programaciones_mantenimiento WHERE codigo = :codigo"), {"codigo": codigo}):
                break
        else:
            raise ApiError(500, "No fue posible generar un código único de programación.")
        item = ProgramacionMantenimiento(
            codigo=codigo,
            id_vehiculo=data.id_vehiculo,
            kilometraje=data.kilometraje,
            fecha=data.fecha,
            tipo=data.tipo.value,
            estado="PROGRAMADO",
        )
        db.add(item)
        db.commit()
        return {
            "codigo": codigo,
            "idVehiculo": data.id_vehiculo,
            "fecha": data.fecha.isoformat(),
            "tipo": data.tipo.value,
            "estado": "PROGRAMADO",
        }
    except ApiError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "La programación entra en conflicto con una existente.") from exc
    except OperationalError as exc:
        db.rollback()
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc
