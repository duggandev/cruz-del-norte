from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.shared.database import SessionLocal
from app.shared.models import Pago


def add_pago(estado="APROBADO", transaccion="chr_0001", reserva=5501):
    with SessionLocal.begin() as db:
        db.add(Pago(id_transaccion=transaccion, id_reserva=reserva, importe_centavos=6500, medio_pago="EFECTIVO", estado=estado))


def emitir(client, headers, transaccion="chr_0001", reserva=5501):
    return client.post("/api/v1/pasajes", json={"idReserva": reserva, "idTransaccion": transaccion}, headers=headers)


def test_emision_aprobada_pdf_y_url(pasajes_client, auth_headers):
    add_pago()
    response = emitir(pasajes_client, auth_headers)
    assert response.status_code == 201
    pdf = pasajes_client.get(response.json()["documentoUrl"].replace("http://testserver", ""))
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


def test_pago_pendiente_y_rechazado(pasajes_client, auth_headers):
    add_pago("PENDIENTE")
    assert emitir(pasajes_client, auth_headers).status_code == 422
    add_pago("RECHAZADO", "chr_rejected")
    assert emitir(pasajes_client, auth_headers, "chr_rejected").status_code == 422


def test_reserva_y_transaccion_inexistentes(pasajes_client, auth_headers):
    assert emitir(pasajes_client, auth_headers, reserva=999).status_code == 404
    assert emitir(pasajes_client, auth_headers).status_code == 422


def test_transaccion_de_otra_reserva(pasajes_client, auth_headers):
    add_pago()
    assert emitir(pasajes_client, auth_headers, reserva=5502).status_code == 422


def test_pasaje_duplicado(pasajes_client, auth_headers):
    add_pago()
    assert emitir(pasajes_client, auth_headers).status_code == 201
    assert emitir(pasajes_client, auth_headers).status_code == 409


def test_token_invalido(pasajes_client):
    assert emitir(pasajes_client, {}).status_code == 401


def test_concurrencia_no_duplica_pasaje(pasajes_client, auth_headers):
    add_pago()
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: emitir(pasajes_client, auth_headers).status_code, range(2)))
    assert sorted(statuses) == [201, 409]
