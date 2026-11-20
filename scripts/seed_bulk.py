import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.shared.config import settings
from app.shared.database import SessionLocal
from app.shared.models import (
    AsientoViaje,
    Pago,
    Pasaje,
    ProgramacionMantenimiento,
    Reserva,
    Vehiculo,
    Viaje,
)


LIMA = ZoneInfo("America/Lima")
TRIP_START = 2000
TRIP_COUNT = 240
SEATS_PER_TRIP = 48
RESERVATIONS_PER_TRIP = 12
RESERVATION_START = 100_000
VEHICLE_START = 100
VEHICLE_COUNT = 60

CITIES = ["Lima", "Ica", "Chimbote", "Trujillo", "Chiclayo", "Piura", "Huaraz", "Arequipa", "Cusco", "Tacna", "Cajamarca", "Huancayo"]
NAMES = ["Ana", "Luis", "María", "Carlos", "Lucía", "Jorge", "Elena", "Miguel", "Sofía", "Diego", "Valeria", "José"]
SURNAMES = ["Rojas Vega", "Pérez Díaz", "García Soto", "Torres Ruiz", "Flores Ramos", "Mendoza León", "Castro Silva", "Vargas Cruz"]
FARES = [3500, 4500, 5500, 6500, 7500, 8500, 9500, 11000, 12500]
DEPARTURES = ["06:00", "07:30", "09:00", "11:30", "14:00", "17:30", "20:00", "22:30"]


def ensure_allowed_environment() -> None:
    if settings.app_env.lower() not in {"academic_demo", "development", "dev"}:
        raise SystemExit("seed_bulk.py solo está habilitado para demostración académica o desarrollo.")


def reservation_id(trip_offset: int, seat: int) -> int:
    return RESERVATION_START + trip_offset * RESERVATIONS_PER_TRIP + seat - 1


def create_seed_pdf(path: Path, code: str, reservation: Reserva, trip: Viaje, payment: Pago) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    pdf.setTitle(f"Pasaje académico {code}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(60, 790, "CRUZ DEL NORTE - DATOS ACADÉMICOS")
    pdf.setFont("Helvetica", 11)
    details = [
        f"Código: {code}",
        f"Pasajero: {reservation.pasajero_nombres} {reservation.pasajero_apellidos}",
        f"DNI ficticio: {reservation.pasajero_dni}",
        f"Ruta: {trip.origen} - {trip.destino}",
        f"Fecha y hora: {trip.fecha.isoformat()} {trip.hora_salida}",
        f"Asiento: {reservation.id_asiento}",
        f"Transacción académica: {payment.id_transaccion}",
    ]
    y = 750
    for line in details:
        pdf.drawString(60, y, line)
        y -= 24
    pdf.save()


def seed_trips_seats_and_vehicles() -> None:
    base_date = date(2026, 11, 15)
    with SessionLocal.begin() as db:
        existing_trips = set(db.scalars(select(Viaje.id_viaje).where(Viaje.id_viaje.between(TRIP_START, TRIP_START + TRIP_COUNT - 1))))
        for offset in range(TRIP_COUNT):
            trip_id = TRIP_START + offset
            if trip_id in existing_trips:
                continue
            origin_index = offset % len(CITIES)
            destination_index = (origin_index + 1 + (offset // len(CITIES)) % (len(CITIES) - 1)) % len(CITIES)
            db.add(Viaje(
                id_viaje=trip_id,
                origen=CITIES[origin_index],
                destino=CITIES[destination_index],
                fecha=base_date + timedelta(days=offset % 120),
                hora_salida=DEPARTURES[offset % len(DEPARTURES)],
                tarifa_centavos=FARES[offset % len(FARES)],
                estado="PROGRAMADO",
            ))
        db.flush()

        existing_seats = set(db.execute(
            select(AsientoViaje.id_viaje, AsientoViaje.id_asiento).where(
                AsientoViaje.id_viaje.between(TRIP_START, TRIP_START + TRIP_COUNT - 1)
            )
        ).all())
        for offset in range(TRIP_COUNT):
            trip_id = TRIP_START + offset
            for seat in range(1, SEATS_PER_TRIP + 1):
                if (trip_id, seat) not in existing_seats:
                    db.add(AsientoViaje(id_viaje=trip_id, id_asiento=seat, estado="DISPONIBLE"))

        existing_vehicles = set(db.scalars(select(Vehiculo.id_vehiculo).where(Vehiculo.id_vehiculo.between(VEHICLE_START, VEHICLE_START + VEHICLE_COUNT - 1))))
        for offset in range(VEHICLE_COUNT):
            vehicle_id = VEHICLE_START + offset
            if vehicle_id not in existing_vehicles:
                db.add(Vehiculo(id_vehiculo=vehicle_id, placa=f"CDN-{vehicle_id:03d}", estado="DISPONIBLE" if offset % 5 else "NO_DISPONIBLE"))

        # Oferta operativa desde hoy y para las siguientes seis semanas.
        # IDs separados para que el sembrado sea idempotente aunque ya exista el lote académico.
        today = date.today()
        current_routes = [("Lima", "Ica"), ("Lima", "Chimbote"), ("Ica", "Lima"), ("Chimbote", "Lima")]
        for day_offset in range(42):
            for route_offset, (origin, destination) in enumerate(current_routes):
                trip_id = 3000 + day_offset * len(current_routes) + route_offset
                if db.get(Viaje, trip_id):
                    continue
                db.add(Viaje(id_viaje=trip_id, origen=origin, destino=destination, fecha=today + timedelta(days=day_offset), hora_salida=DEPARTURES[route_offset], tarifa_centavos=6500 + route_offset * 500, estado="PROGRAMADO"))
        db.flush()
        for day_offset in range(42):
            for route_offset in range(len(current_routes)):
                trip_id = 3000 + day_offset * len(current_routes) + route_offset
                if not db.get(AsientoViaje, (trip_id, 1)):
                    for seat in range(1, SEATS_PER_TRIP + 1):
                        db.add(AsientoViaje(id_viaje=trip_id, id_asiento=seat, estado="DISPONIBLE"))


def seed_reservations() -> None:
    with SessionLocal() as query_db:
        existing = set(query_db.scalars(
            select(Reserva.id_reserva).where(Reserva.id_reserva.between(RESERVATION_START, RESERVATION_START + TRIP_COUNT * RESERVATIONS_PER_TRIP - 1))
        ))
    with SessionLocal.begin() as db:
        trips = {trip.id_viaje: trip for trip in db.scalars(select(Viaje).where(Viaje.id_viaje.between(TRIP_START, TRIP_START + TRIP_COUNT - 1)))}
        for offset in range(TRIP_COUNT):
            trip = trips[TRIP_START + offset]
            departure = datetime.combine(trip.fecha, time.fromisoformat(trip.hora_salida), tzinfo=LIMA)
            for seat in range(1, RESERVATIONS_PER_TRIP + 1):
                item_id = reservation_id(offset, seat)
                if item_id in existing:
                    continue
                category = (seat - 1) % 4
                state = ("CONFIRMADA", "TEMPORAL", "VENCIDA", "CANCELADA")[category]
                expiration = departure - timedelta(hours=1)
                if state in {"VENCIDA", "CANCELADA"}:
                    expiration = datetime(2026, 11, 1, 12, 0, tzinfo=LIMA)
                person_index = (offset + seat) % len(NAMES)
                db.add(Reserva(
                    id_reserva=item_id,
                    id_viaje=trip.id_viaje,
                    id_asiento=seat,
                    id_canal=(seat % 3) + 1,
                    pasajero_dni=f"{70_000_000 + (item_id % 9_999_999):08d}",
                    pasajero_nombres=NAMES[person_index],
                    pasajero_apellidos=SURNAMES[(offset + seat) % len(SURNAMES)],
                    estado=state,
                    vencimiento=expiration.replace(tzinfo=None),
                ))


def seed_payments_and_tickets() -> None:
    with SessionLocal.begin() as db:
        trips = {trip.id_viaje: trip for trip in db.scalars(select(Viaje).where(Viaje.id_viaje.between(TRIP_START, TRIP_START + TRIP_COUNT - 1)))}
        existing_transactions = set(db.scalars(select(Pago.id_transaccion).where(Pago.id_transaccion.like("SEED-%"))))
        for offset in range(TRIP_COUNT):
            trip = trips[TRIP_START + offset]
            for seat in range(1, RESERVATIONS_PER_TRIP + 1):
                item_id = reservation_id(offset, seat)
                category = (seat - 1) % 4
                if category not in {0, 2}:
                    continue
                prefix = "APP" if category == 0 else "REJ"
                transaction = f"SEED-{prefix}-{item_id}"
                if transaction not in existing_transactions:
                    db.add(Pago(
                        id_transaccion=transaction,
                        id_reserva=item_id,
                        importe_centavos=trip.tarifa_centavos,
                        medio_pago="PASARELA",
                        estado="APROBADO" if category == 0 else "RECHAZADO",
                        proveedor="ACADEMIC_SEED",
                        referencia_proveedor=f"SEED_REF-{item_id}",
                    ))
        db.flush()

        existing_codes = set(db.scalars(select(Pasaje.codigo).where(Pasaje.codigo.like("CDN-SEED-%"))))
        approved_payments = {
            payment.id_reserva: payment
            for payment in db.scalars(select(Pago).where(Pago.id_transaccion.like("SEED-APP-%")))
        }
        for offset in range(TRIP_COUNT):
            for seat in range(1, RESERVATIONS_PER_TRIP + 1):
                if (seat - 1) % 4 != 0:
                    continue
                item_id = reservation_id(offset, seat)
                code = f"CDN-SEED-{item_id}"
                if code in existing_codes:
                    continue
                reservation = db.get(Reserva, item_id)
                payment = approved_payments.get(item_id)
                if not reservation or not payment:
                    continue
                trip = trips[reservation.id_viaje]
                pdf_path = settings.pasajes_directory / f"{code}.pdf"
                create_seed_pdf(pdf_path, code, reservation, trip, payment)
                db.add(Pasaje(
                    codigo=code,
                    id_reserva=item_id,
                    id_pago=payment.id_pago,
                    estado="EMITIDO",
                    fecha_emision=datetime(2026, 11, 13, 9, 0, tzinfo=LIMA),
                    documento_url=f"{settings.public_pasajes_url.rstrip('/')}/{code}.pdf",
                    documento_path=str(pdf_path),
                ))


def seed_maintenance() -> None:
    with SessionLocal.begin() as db:
        existing = set(db.scalars(select(ProgramacionMantenimiento.codigo).where(ProgramacionMantenimiento.codigo.like("SEED-PRG-%"))))
        base_date = date(2026, 11, 20)
        for vehicle_offset in range(VEHICLE_COUNT):
            vehicle_id = VEHICLE_START + vehicle_offset
            for schedule_offset in range(10):
                code = f"SEED-PRG-{vehicle_id:03d}-{schedule_offset + 1:02d}"
                if code in existing:
                    continue
                db.add(ProgramacionMantenimiento(
                    codigo=code,
                    id_vehiculo=vehicle_id,
                    kilometraje=40_000 + vehicle_offset * 2_500 + schedule_offset * 5_000,
                    fecha=base_date + timedelta(days=schedule_offset * 14 + vehicle_offset % 7),
                    tipo="PREVENTIVO" if schedule_offset % 3 else "CORRECTIVO",
                    estado="PROGRAMADO",
                ))


def main() -> None:
    ensure_allowed_environment()
    seed_trips_seats_and_vehicles()
    seed_reservations()
    seed_payments_and_tickets()
    seed_maintenance()
    print("Carga académica masiva completada de forma idempotente.")


if __name__ == "__main__":
    main()
