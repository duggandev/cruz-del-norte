from sqlalchemy import select

from app.shared.config import settings
from app.shared.database import SessionLocal
from app.shared.models import Pago


def pagar_mock(client, headers, token, key="mock-key"):
    return client.post(
        "/api/v1/pagos",
        json={"idReserva": 5501, "importe": 65.00, "medioPago": "PASARELA", "tokenPasarela": token},
        headers={**headers, "Idempotency-Key": key},
    )


def test_mock_aprobado_persiste_como_simulado(pagos_client, auth_headers):
    response = pagar_mock(pagos_client, auth_headers, "mock_aprobado")
    assert response.status_code == 201
    assert response.json()["estado"] == "APROBADO"
    assert response.json()["idTransaccion"] == "MOCK-000001"
    with SessionLocal() as db:
        pago = db.scalar(select(Pago).where(Pago.id_transaccion == response.json()["idTransaccion"]))
        assert pago.proveedor == "MOCK_GATEWAY"
        assert pago.referencia_proveedor == "MOCK_REF-000001"


def test_mock_rechazado(pagos_client, auth_headers):
    response = pagar_mock(pagos_client, auth_headers, "mock_rechazado")
    assert response.status_code == 201
    assert response.json()["estado"] == "RECHAZADO"


def test_mock_pendiente(pagos_client, auth_headers):
    response = pagar_mock(pagos_client, auth_headers, "mock_pendiente")
    assert response.status_code == 202
    assert response.json()["estado"] == "PENDIENTE"


def test_mock_genera_secuencia_correlativa(pagos_client, auth_headers):
    first = pagar_mock(pagos_client, auth_headers, "mock_rechazado", "sequence-1")
    second = pagar_mock(pagos_client, auth_headers, "mock_pendiente", "sequence-2")
    assert first.json()["idTransaccion"] == "MOCK-000001"
    assert second.json()["idTransaccion"] == "MOCK-000002"


def test_mock_error_y_timeout_no_persisten(pagos_client, auth_headers):
    assert pagar_mock(pagos_client, auth_headers, "mock_error", "error-key").status_code == 502
    assert pagar_mock(pagos_client, auth_headers, "mock_timeout", "timeout-key").status_code == 504
    with SessionLocal() as db:
        assert db.scalar(select(Pago.id_pago).limit(1)) is None


def test_mock_token_desconocido(pagos_client, auth_headers):
    assert pagar_mock(pagos_client, auth_headers, "token_real_no_permitido").status_code == 422


def test_mock_idempotencia(pagos_client, auth_headers):
    first = pagar_mock(pagos_client, auth_headers, "mock_rechazado", "same-mock")
    retry = pagar_mock(pagos_client, auth_headers, "mock_rechazado", "same-mock")
    conflict = pagar_mock(pagos_client, auth_headers, "mock_pendiente", "same-mock")
    assert first.status_code == retry.status_code == 201
    assert first.json() == retry.json()
    assert conflict.status_code == 409


def test_mock_bloqueado_en_produccion(pagos_client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    response = pagar_mock(pagos_client, auth_headers, "mock_aprobado")
    assert response.status_code == 503


def test_mock_requiere_habilitacion_explicita(pagos_client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "payment_mock_enabled", False)
    response = pagar_mock(pagos_client, auth_headers, "mock_aprobado")
    assert response.status_code == 503


def test_mock_funciona_con_red_bloqueada(pagos_client, auth_headers, monkeypatch):
    import socket

    def deny_network(*_args, **_kwargs):
        raise AssertionError("El simulador intentó acceder a la red")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    response = pagar_mock(pagos_client, auth_headers, "mock_aprobado", "offline-key")
    assert response.status_code == 201
    assert response.json()["idTransaccion"] == "MOCK-000001"


def test_sc05_acepta_solo_mock_aprobado(pagos_client, pasajes_client, auth_headers):
    approved = pagar_mock(pagos_client, auth_headers, "mock_aprobado", "ticket-approved")
    ticket = pasajes_client.post(
        "/api/v1/pasajes",
        json={"idReserva": 5501, "idTransaccion": approved.json()["idTransaccion"]},
        headers=auth_headers,
    )
    assert ticket.status_code == 201


def test_sc05_rechaza_mock_rechazado(pagos_client, pasajes_client, auth_headers):
    rejected = pagar_mock(pagos_client, auth_headers, "mock_rechazado", "ticket-rejected")
    ticket = pasajes_client.post(
        "/api/v1/pasajes",
        json={"idReserva": 5501, "idTransaccion": rejected.json()["idTransaccion"]},
        headers=auth_headers,
    )
    assert ticket.status_code == 422


def test_sc05_rechaza_mock_pendiente(pagos_client, pasajes_client, auth_headers):
    pending = pagar_mock(pagos_client, auth_headers, "mock_pendiente", "ticket-pending")
    ticket = pasajes_client.post(
        "/api/v1/pasajes",
        json={"idReserva": 5501, "idTransaccion": pending.json()["idTransaccion"]},
        headers=auth_headers,
    )
    assert ticket.status_code == 422
