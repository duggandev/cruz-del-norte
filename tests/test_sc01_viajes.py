def test_disponibilidad_excluye_reservas_activas(viajes_client, auth_headers):
    response = viajes_client.get(
        "/api/v1/viajes/disponibilidad",
        params={"origen": "Lima", "destino": "Ica", "fecha": "2030-12-01"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    viaje = response.json()["viajes"][0]
    assert viaje["tarifa"] == 65.0
    assert 12 not in viaje["asientosDisponibles"]
    assert 13 not in viaje["asientosDisponibles"]
    assert 14 in viaje["asientosDisponibles"]


def test_disponibilidad_sin_resultados(viajes_client, auth_headers):
    response = viajes_client.get(
        "/api/v1/viajes/disponibilidad",
        params={"origen": "Lima", "destino": "Cusco", "fecha": "2030-12-01"},
        headers=auth_headers,
    )
    assert response.status_code == 204


def test_disponibilidad_valida_parametros_y_token(viajes_client, auth_headers):
    params = {"origen": "Lima", "destino": "Lima", "fecha": "2030-12-01"}
    assert viajes_client.get("/api/v1/viajes/disponibilidad", params=params, headers=auth_headers).status_code == 400
    assert viajes_client.get("/api/v1/viajes/disponibilidad", params=params).status_code == 401
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.shared.database import SessionLocal
from app.shared.models import Reserva




def test_reserva_vencida_deja_de_bloquear(viajes_client, auth_headers):
    with SessionLocal.begin() as db:
        db.get(Reserva, 5501).vencimiento = datetime.now(ZoneInfo("America/Lima")) - timedelta(minutes=1)
    response = viajes_client.get(
        "/api/v1/viajes/disponibilidad",
        params={"origen": "Lima", "destino": "Ica", "fecha": "2030-12-01"},
        headers=auth_headers,
    )
    assert 12 in response.json()["viajes"][0]["asientosDisponibles"]
