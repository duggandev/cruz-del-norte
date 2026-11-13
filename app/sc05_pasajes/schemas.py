from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PasajeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_reserva: int = Field(alias="idReserva", gt=0)
    id_transaccion: str = Field(alias="idTransaccion", min_length=1, max_length=80)


class PasajeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    codigo: str
    id_reserva: int = Field(alias="idReserva")
    estado: str
    fecha_emision: datetime = Field(alias="fechaEmision")
    documento_url: str = Field(alias="documentoUrl")
