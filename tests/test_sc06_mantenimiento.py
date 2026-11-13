from concurrent.futures import ThreadPoolExecutor


def programar(client, headers, **changes):
    body = {"idVehiculo": 14, "kilometraje": 120500, "fecha": "2030-12-10", "tipo": "PREVENTIVO"}
    body.update(changes)
    return client.post("/api/v1/programaciones", json=body, headers=headers)


def test_programacion_preventiva(mantenimiento_client, auth_headers):
    response = programar(mantenimiento_client, auth_headers)
    assert response.status_code == 201
    assert response.json()["codigo"].startswith("PRG-")


def test_programacion_correctiva(mantenimiento_client, auth_headers):
    assert programar(mantenimiento_client, auth_headers, tipo="CORRECTIVO").status_code == 201


def test_vehiculo_inexistente(mantenimiento_client, auth_headers):
    assert programar(mantenimiento_client, auth_headers, idVehiculo=99).status_code == 404


def test_fecha_pasada_y_kilometraje_negativo(mantenimiento_client, auth_headers):
    assert programar(mantenimiento_client, auth_headers, fecha="2020-01-01").status_code == 422
    assert programar(mantenimiento_client, auth_headers, kilometraje=-1).status_code == 400


def test_duplicada_y_otra_fecha(mantenimiento_client, auth_headers):
    assert programar(mantenimiento_client, auth_headers).status_code == 201
    assert programar(mantenimiento_client, auth_headers).status_code == 409
    assert programar(mantenimiento_client, auth_headers, fecha="2030-12-11").status_code == 201


def test_token_invalido(mantenimiento_client):
    assert programar(mantenimiento_client, {}).status_code == 401


def test_concurrencia_no_duplica_programacion(mantenimiento_client, auth_headers):
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: programar(mantenimiento_client, auth_headers).status_code, range(2)))
    assert sorted(statuses) == [201, 409]
