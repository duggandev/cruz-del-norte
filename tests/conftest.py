import os
import shutil
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


TEST_ROOT = Path(__file__).resolve().parent / ".runtime"
TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["APP_ENV"] = "development"
os.environ["DATABASE_PATH"] = str(TEST_ROOT / "test.db")
os.environ["STORAGE_PASAJES_PATH"] = str(TEST_ROOT / "pasajes")
os.environ["PUBLIC_PASAJES_URL"] = "http://testserver/documentos"
os.environ["JWT_SECRET_KEY"] = "test-secret-only-at-least-thirty-two-bytes-long"
os.environ["PAYMENT_PROVIDER"] = "mock"
os.environ["PAYMENT_MOCK_ENABLED"] = "true"

from fastapi.testclient import TestClient

from app.sc04_pagos.main import app as pagos_app
from app.sc05_pasajes.main import app as pasajes_app
from app.sc06_mantenimiento.main import app as mantenimiento_app
from app.sc01_viajes.main import app as viajes_app
from app.sc02_reservas.main import app as reservas_app
from app.sc03_pasajeros.main import app as pasajeros_app
from app.shared.database import Base, SessionLocal, engine
from app.shared.models import AsientoViaje, Reserva, Vehiculo, Viaje
from app.shared.security import create_access_token


Base.metadata.create_all(engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_runtime():
    yield
    engine.dispose()
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    with SessionLocal.begin() as db:
        db.add(Viaje(id_viaje=1021, origen="Lima", destino="Ica", fecha=date(2030, 12, 1), hora_salida="10:00", tarifa_centavos=6500, estado="PROGRAMADO"))
        db.flush()
        db.add_all([
            Reserva(id_reserva=5501, id_viaje=1021, id_asiento=12, id_canal=1, pasajero_dni="45871236", pasajero_nombres="Ana", pasajero_apellidos="Rojas Vega", estado="TEMPORAL", vencimiento=datetime(2030, 12, 1, 10, 25, tzinfo=ZoneInfo("America/Lima"))),
            Reserva(id_reserva=5502, id_viaje=1021, id_asiento=13, id_canal=1, pasajero_dni="40000000", pasajero_nombres="Luis", pasajero_apellidos="Pérez", estado="TEMPORAL", vencimiento=datetime(2030, 12, 1, 10, 25, tzinfo=ZoneInfo("America/Lima"))),
        ])
        db.add(Vehiculo(id_vehiculo=14, placa="ABC-123", estado="DISPONIBLE"))
        db.add_all([AsientoViaje(id_viaje=1021, id_asiento=numero, estado="DISPONIBLE") for numero in range(1, 21)])
    yield


@pytest.fixture
def auth_headers():
    token = create_access_token("tester", ["ADMIN"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pagos_client():
    return TestClient(pagos_app)


@pytest.fixture
def viajes_client():
    return TestClient(viajes_app)


@pytest.fixture
def reservas_client():
    return TestClient(reservas_app)


@pytest.fixture
def pasajeros_client():
    return TestClient(pasajeros_app)


@pytest.fixture
def pasajes_client():
    return TestClient(pasajes_app)


@pytest.fixture
def mantenimiento_client():
    return TestClient(mantenimiento_app)
