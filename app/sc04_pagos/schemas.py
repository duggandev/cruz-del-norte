from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class MedioPago(StrEnum):
    EFECTIVO = "EFECTIVO"
    POS = "POS"
    PASARELA = "PASARELA"
    TERCERO = "TERCERO"


class PagoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_reserva: int = Field(alias="idReserva", gt=0)
    importe: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    medio_pago: MedioPago = Field(alias="medioPago")
    token_pasarela: str | None = Field(default=None, alias="tokenPasarela", min_length=1, max_length=500)
    referencia_pos: str | None = Field(default=None, alias="referenciaPos", min_length=1, max_length=120)

    @model_validator(mode="after")
    def require_payment_reference(self):
        if self.medio_pago == MedioPago.PASARELA and not self.token_pasarela:
            raise ValueError("tokenPasarela es obligatorio para PASARELA")
        if self.medio_pago == MedioPago.POS and not self.referencia_pos:
            raise ValueError("referenciaPos es obligatorio para POS")
        return self


class PagoResponse(BaseModel):
    id_transaccion: str = Field(alias="idTransaccion")
    id_reserva: int = Field(alias="idReserva")
    importe: Decimal
    estado: str

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("importe")
    def serialize_importe(self, value: Decimal) -> float:
        return float(value)
