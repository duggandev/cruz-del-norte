from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

class ViajeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    id_viaje: int | None = Field(default=None, alias="idViaje", gt=0)
    origen: str = Field(min_length=1, max_length=120)
    destino: str = Field(min_length=1, max_length=120)
    fecha: date
    hora_salida: str = Field(alias="horaSalida", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    tarifa: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    tipo_bus: str = Field(default="DOS_PISOS_48", alias="tipoBus", pattern="^(DOS_PISOS_48|UN_PISO_48)$")
    estado: str = Field(default="PROGRAMADO", pattern="^(PROGRAMADO|DISPONIBLE)$")


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
