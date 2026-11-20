from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ValidacionPasajeroRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(max_length=30)
    nombres: str = Field(max_length=120)
    apellidos: str = Field(max_length=120)
    correo: str | None = Field(default=None, max_length=254)
    fecha_nacimiento: date | None = Field(default=None, alias="fechaNacimiento")
    viaja_solo: bool = Field(default=False, alias="viajaSolo")
    permiso_notarial: bool = Field(default=False, alias="permisoNotarial")
    acompanante_mayor_edad: bool = Field(default=False, alias="acompananteMayorEdad")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ValidacionPasajeroResponse(BaseModel):
    resultado: str
    observaciones: list[str]
