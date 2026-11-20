import re
from datetime import date

from app.sc03_pasajeros import repository
from app.sc03_pasajeros.schemas import ValidacionPasajeroRequest

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def validar_pasajero(data: ValidacionPasajeroRequest) -> tuple[dict, int]:
    observaciones: list[str] = []
    if not re.fullmatch(r"\d{8}", data.dni): observaciones.append("El DNI debe contener exactamente ocho numeros.")
    if not data.nombres.strip(): observaciones.append("Los nombres son obligatorios.")
    if not data.apellidos.strip(): observaciones.append("Los apellidos son obligatorios.")
    if data.correo is not None and not EMAIL_PATTERN.fullmatch(data.correo.strip()): observaciones.append("El correo no cumple el formato requerido.")
    if data.fecha_nacimiento:
        today = date.today()
        edad = today.year - data.fecha_nacimiento.year - ((today.month, today.day) < (data.fecha_nacimiento.month, data.fecha_nacimiento.day))
        if edad < 0 or edad > 120: observaciones.append("La fecha de nacimiento no es valida.")
        elif edad < 12 and (data.viaja_solo or not data.acompanante_mayor_edad): observaciones.append("Los menores de 12 anos deben viajar acompanados por un adulto autorizado.")
        elif edad < 18 and not data.permiso_notarial: observaciones.append("Los menores que viajan sin sus padres requieren permiso notarial.")
    body = {"resultado": "OBSERVADO" if observaciones else "CONFORME", "observaciones": observaciones}
    return body, (200 if repository.official_identity_provider_available() else 203)

def politicas_viaje() -> dict:
    return {"edadMinimaViajeSolo": 12, "permisoNotarialRequeridoDesde": 12, "permisoNotarialRequeridoCuando": "el menor viaja sin sus padres", "anticipacionEmbarqueMinutos": 30, "reembolso": {"tarifaRegular": {"maxHorasAntes": 12, "penalidadPorcentaje": 0}, "tarifaPromocional": {"disponible": False}}, "cambio": {"tarifaRegular": {"maxHorasAntes": 6, "costo": "diferencia_tarifaria_si_corresponde"}}, "fuente": "Condiciones publicas de transporte de Cruz del Sur; validar contrato vigente de Cruz del Norte antes de produccion."}
