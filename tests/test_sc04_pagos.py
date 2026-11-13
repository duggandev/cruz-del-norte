from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.shared.database import SessionLocal
from app.shared.models import Reserva


def request_pago(client, headers, key="pago-1", **changes):
    body = {"idReserva": 5501, "importe": 65.00, "medioPago": "EFECTIVO"}
    body.update(changes)
    return client.post("/api/v1/pagos", json=body, headers={**headers, "Idempotency-Key": key})


def test_pago_efectivo_aprobado(pagos_client, auth_headers):
    response = request_pago(pagos_client, auth_headers)
    assert response.status_code == 201
    assert response.json()["estado"] == "APROBADO"


def test_importe_incorrecto(pagos_client, auth_headers):
    response = request_pago(pagos_client, auth_headers, importe=60)
    assert response.status_code == 422


def test_reserva_inexistente(pagos_client, auth_headers):
    response = request_pago(pagos_client, auth_headers, idReserva=9999)
    assert response.status_code == 404


def test_reserva_vencida(pagos_client, auth_headers):
    with SessionLocal.begin() as db:
        reserva = db.get(Reserva, 5501)
        reserva.vencimiento = datetime.now(ZoneInfo("America/Lima")) - timedelta(minutes=1)
    assert request_pago(pagos_client, auth_headers).status_code == 410


def test_pago_duplicado(pagos_client, auth_headers):
    assert request_pago(pagos_client, auth_headers, "uno").status_code == 201
    assert request_pago(pagos_client, auth_headers, "dos").status_code == 409


def test_idempotencia_repite_respuesta(pagos_client, auth_headers):
    first = request_pago(pagos_client, auth_headers, "misma")
    second = request_pago(pagos_client, auth_headers, "misma")
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


def test_idempotencia_conflicto(pagos_client, auth_headers):
    assert request_pago(pagos_client, auth_headers, "misma").status_code == 201
    assert request_pago(pagos_client, auth_headers, "misma", importe=64).status_code == 409


def test_pasarela_pendiente_y_rechazada(pagos_client, auth_headers):
    pending = request_pago(pagos_client, auth_headers, "pending", medioPago="PASARELA", tokenPasarela="mock_pendiente")
    rejected = request_pago(pagos_client, auth_headers, "rejected", medioPago="PASARELA", tokenPasarela="mock_rechazado")
    assert pending.status_code == 202 and pending.json()["estado"] == "PENDIENTE"
    assert rejected.status_code == 201 and rejected.json()["estado"] == "RECHAZADO"


def test_tercero_no_implementado(pagos_client, auth_headers):
    assert request_pago(pagos_client, auth_headers, medioPago="TERCERO").status_code == 501


def test_token_invalido_y_clave_ausente(pagos_client, auth_headers):
    assert pagos_client.post("/api/v1/pagos", json={}).status_code == 401
    response = pagos_client.post("/api/v1/pagos", json={"idReserva": 5501, "importe": 65, "medioPago": "EFECTIVO"}, headers=auth_headers)
    assert response.status_code == 400


def test_concurrencia_no_duplica_cobro(pagos_client, auth_headers):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda key: request_pago(pagos_client, auth_headers, key).status_code, ["c1", "c2"]))
    assert sorted(results) == [201, 409]
