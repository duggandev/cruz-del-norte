import pytest


@pytest.mark.parametrize(
    "client_fixture",
    [
        "viajes_client",
        "reservas_client",
        "pasajeros_client",
        "pagos_client",
        "pasajes_client",
        "mantenimiento_client",
    ],
)
def test_health_endpoint_is_public_and_reports_ok(request, client_fixture):
    client = request.getfixturevalue(client_fixture)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
