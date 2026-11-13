from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TipoMantenimiento(StrEnum):
    PREVENTIVO = "PREVENTIVO"
    CORRECTIVO = "CORRECTIVO"


class ProgramacionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_vehiculo: int = Field(alias="idVehiculo", gt=0)
    kilometraje: int = Field(ge=0)
    fecha: date
    tipo: TipoMantenimiento


class ProgramacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    codigo: str
    id_vehiculo: int = Field(alias="idVehiculo")
    fecha: date
    tipo: TipoMantenimiento
    estado: str
