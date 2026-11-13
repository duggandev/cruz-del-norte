import re

from app.sc03_pasajeros import repository
from app.sc03_pasajeros.schemas import ValidacionPasajeroRequest


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validar_pasajero(data: ValidacionPasajeroRequest) -> tuple[dict, int]:
    observaciones: list[str] = []
    if not re.fullmatch(r"\d{8}", data.dni):
        observaciones.append("El DNI no cumple con el formato requerido.")
    if not data.nombres.strip():
        observaciones.append("Los nombres son obligatorios.")
    if not data.apellidos.strip():
        observaciones.append("Los apellidos son obligatorios.")
    if data.correo is not None and not EMAIL_PATTERN.fullmatch(data.correo.strip()):
        observaciones.append("El correo electrónico no cumple con el formato requerido.")
    body = {"resultado": "OBSERVADO" if observaciones else "CONFORME", "observaciones": observaciones}
    # Sin integración oficial, el contrato exige 203 incluso si el formato es conforme.
    status = 200 if repository.official_identity_provider_available() else 203
    return body, status
