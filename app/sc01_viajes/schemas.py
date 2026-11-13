from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ViajeDisponible(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_viaje: int = Field(alias="idViaje")
    hora_salida: str = Field(alias="horaSalida")
    tarifa: Decimal
    asientos_disponibles: list[int] = Field(alias="asientosDisponibles")

    @field_serializer("tarifa")
    def serialize_tarifa(self, value: Decimal) -> float:
        return float(value)


class DisponibilidadResponse(BaseModel):
    origen: str
    destino: str
    fecha: date
    viajes: list[ViajeDisponible]
