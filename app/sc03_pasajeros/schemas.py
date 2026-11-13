from pydantic import BaseModel, ConfigDict, Field


class ValidacionPasajeroRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(max_length=30)
    nombres: str = Field(max_length=120)
    apellidos: str = Field(max_length=120)
    correo: str | None = Field(default=None, max_length=254)


class ValidacionPasajeroResponse(BaseModel):
    resultado: str
    observaciones: list[str]
