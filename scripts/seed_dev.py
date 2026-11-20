import sys
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.shared.config import settings
from app.shared.database import SessionLocal
from app.shared.models import AsientoViaje, Reserva, Vehiculo, Viaje


def main() -> None:
    if settings.app_env.lower() not in {"academic_demo", "development", "dev"}:
        raise SystemExit("seed_dev.py solo puede ejecutarse en desarrollo.")
    lima = ZoneInfo("America/Lima")
    with SessionLocal.begin() as db:
        if not db.get(Viaje, 1021):
            db.add(Viaje(id_viaje=1021, origen="Lima", destino="Ica", fecha=date(2026, 12, 1), hora_salida="10:00", tarifa_centavos=6500, estado="PROGRAMADO", tipo_bus="DOS_PISOS_48", pisos=2, capacidad=60))
            db.flush()
        if not db.get(Viaje, 1022):
            db.add(Viaje(id_viaje=1022, origen="Chimbote", destino="Lima", fecha=date(2026, 12, 15), hora_salida="08:30", tarifa_centavos=6500, estado="PROGRAMADO", tipo_bus="UN_PISO_48", pisos=1, capacidad=48))
            db.flush()
        if not db.get(Reserva, 5501):
            db.add(Reserva(id_reserva=5501, id_viaje=1021, id_asiento=12, id_canal=1, pasajero_dni="45871236", pasajero_nombres="Ana", pasajero_apellidos="Rojas Vega", estado="TEMPORAL", vencimiento=datetime(2026, 12, 1, 10, 25, tzinfo=lima)))
        if not db.get(Vehiculo, 14):
            db.add(Vehiculo(id_vehiculo=14, placa="ABC-123", estado="DISPONIBLE"))
        for id_viaje in (1021, 1022):
            for numero in range(1, 61 if id_viaje == 1021 else 49):
                if not db.get(AsientoViaje, (id_viaje, numero)):
                    db.add(AsientoViaje(id_viaje=id_viaje, id_asiento=numero, estado="DISPONIBLE"))
    print("Datos de desarrollo insertados (operación idempotente).")


if __name__ == "__main__":
    main()
