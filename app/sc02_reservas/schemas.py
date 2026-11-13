from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PasajeroReserva(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(min_length=1, max_length=20)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)


class ReservaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_viaje: int = Field(alias="idViaje", gt=0)
    id_asiento: int = Field(alias="idAsiento", gt=0)
    id_canal: int = Field(alias="idCanal", ge=1, le=4)
    pasajero: PasajeroReserva


class ReservaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_reserva: int = Field(alias="idReserva")
    id_viaje: int = Field(alias="idViaje")
    id_asiento: int = Field(alias="idAsiento")
    estado: str
    vencimiento: datetime


class LiberacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_reserva: int = Field(alias="idReserva")
    estado: str
