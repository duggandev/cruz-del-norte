from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PasajeroReserva(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(min_length=1, max_length=20)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    fecha_nacimiento: date | None = Field(default=None, alias="fechaNacimiento")
    viaja_solo: bool = Field(default=False, alias="viajaSolo")
    permiso_notarial: bool = Field(default=False, alias="permisoNotarial")
    acompanante_mayor_edad: bool = Field(default=False, alias="acompananteMayorEdad")
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


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

class ReservaMultipleItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id_asiento: int = Field(alias="idAsiento", gt=0)
    pasajero: PasajeroReserva

class ReservaMultipleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id_viaje: int = Field(alias="idViaje", gt=0)
    id_canal: int = Field(alias="idCanal", ge=1, le=4)
    pasajeros: list[ReservaMultipleItem] = Field(min_length=1, max_length=10)

class ReservaMultipleResponse(BaseModel):
    reservas: list[ReservaResponse]
    cantidad: int


class LiberacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_reserva: int = Field(alias="idReserva")
    estado: str
