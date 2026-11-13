from concurrent.futures import ThreadPoolExecutor

from app.shared.database import SessionLocal
from app.shared.models import Pago


def reservar(client, headers, asiento=14, canal=1):
    return client.post(
        "/api/v1/reservas",
        json={
            "idViaje": 1021,
            "idAsiento": asiento,
            "idCanal": canal,
            "pasajero": {"dni": "45871236", "nombres": "Ana", "apellidos": "Rojas Vega"},
        },
        headers=headers,
    )


def test_registrar_y_liberar_reserva(reservas_client, auth_headers):
    created = reservar(reservas_client, auth_headers)
    assert created.status_code == 201
    reservation_id = created.json()["idReserva"]
    released = reservas_client.post(f"/api/v1/reservas/{reservation_id}/liberacion", headers=auth_headers)
    assert released.status_code == 200
    assert released.json()["estado"] == "CANCELADA"
    assert reservar(reservas_client, auth_headers).status_code == 201


def test_reserva_duplicada_y_canal_externo(reservas_client, auth_headers):
    assert reservar(reservas_client, auth_headers).status_code == 201
    assert reservar(reservas_client, auth_headers).status_code == 409
    assert reservar(reservas_client, auth_headers, asiento=15, canal=4).status_code == 501


def test_viaje_asiento_y_token_invalidos(reservas_client, auth_headers):
    body = {"idViaje": 999, "idAsiento": 1, "idCanal": 1, "pasajero": {"dni": "45871236", "nombres": "Ana", "apellidos": "Rojas"}}
    assert reservas_client.post("/api/v1/reservas", json=body, headers=auth_headers).status_code == 404
    assert reservar(reservas_client, auth_headers, asiento=99).status_code == 404
    assert reservar(reservas_client, {}).status_code == 401


def test_concurrencia_bloquea_un_solo_asiento(reservas_client, auth_headers):
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: reservar(reservas_client, auth_headers, asiento=16).status_code, range(2)))
    assert sorted(statuses) == [201, 409]


def test_no_libera_reserva_pagada(reservas_client, auth_headers):
    created = reservar(reservas_client, auth_headers, asiento=17)
    reservation_id = created.json()["idReserva"]
    with SessionLocal.begin() as db:
        db.add(Pago(id_transaccion="paid_release", id_reserva=reservation_id, importe_centavos=6500, medio_pago="EFECTIVO", estado="APROBADO"))
    response = reservas_client.post(f"/api/v1/reservas/{reservation_id}/liberacion", headers=auth_headers)
    assert response.status_code == 409
