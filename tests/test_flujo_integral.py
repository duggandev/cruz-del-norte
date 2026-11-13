from app.shared.database import SessionLocal
from app.shared.models import Reserva


def test_flujo_comercial_completo(
    viajes_client, pasajeros_client, reservas_client, pagos_client, pasajes_client, auth_headers
):
    query = {"origen": "Lima", "destino": "Ica", "fecha": "2030-12-01"}
    available = viajes_client.get("/api/v1/viajes/disponibilidad", params=query, headers=auth_headers)
    assert 14 in available.json()["viajes"][0]["asientosDisponibles"]

    validation = pasajeros_client.post(
        "/api/v1/pasajeros/validaciones",
        json={"dni": "45871236", "nombres": "Ana", "apellidos": "Rojas Vega", "correo": "ana@example.com"},
        headers=auth_headers,
    )
    assert validation.status_code == 203 and validation.json()["resultado"] == "CONFORME"

    reservation = reservas_client.post(
        "/api/v1/reservas",
        json={"idViaje": 1021, "idAsiento": 14, "idCanal": 1, "pasajero": {"dni": "45871236", "nombres": "Ana", "apellidos": "Rojas Vega"}},
        headers=auth_headers,
    )
    reservation_id = reservation.json()["idReserva"]
    after = viajes_client.get("/api/v1/viajes/disponibilidad", params=query, headers=auth_headers)
    assert 14 not in after.json()["viajes"][0]["asientosDisponibles"]

    payment = pagos_client.post(
        "/api/v1/pagos",
        json={"idReserva": reservation_id, "importe": 65.0, "medioPago": "EFECTIVO"},
        headers={**auth_headers, "Idempotency-Key": f"integral-{reservation_id}"},
    )
    assert payment.status_code == 201
    with SessionLocal() as db:
        assert db.get(Reserva, reservation_id).estado == "CONFIRMADA"

    ticket = pasajes_client.post(
        "/api/v1/pasajes",
        json={"idReserva": reservation_id, "idTransaccion": payment.json()["idTransaccion"]},
        headers=auth_headers,
    )
    assert ticket.status_code == 201
    document = pasajes_client.get(ticket.json()["documentoUrl"].replace("http://testserver", ""))
    assert document.status_code == 200 and document.content.startswith(b"%PDF")
