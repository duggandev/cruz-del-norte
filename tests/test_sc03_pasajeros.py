def validar(client, headers, **changes):
    body = {"dni": "45871236", "nombres": "Ana", "apellidos": "Rojas Vega", "correo": "ana.rojas@example.com"}
    body.update(changes)
    return client.post("/api/v1/pasajeros/validaciones", json=body, headers=headers)


def test_validacion_interna_conforme_usa_203(pasajeros_client, auth_headers):
    response = validar(pasajeros_client, auth_headers)
    assert response.status_code == 203
    assert response.json() == {"resultado": "CONFORME", "observaciones": []}


def test_validacion_observada(pasajeros_client, auth_headers):
    response = validar(pasajeros_client, auth_headers, dni="12A", nombres=" ", correo="incorrecto")
    assert response.status_code == 203
    assert response.json()["resultado"] == "OBSERVADO"
    assert len(response.json()["observaciones"]) == 3


def test_validacion_requiere_token(pasajeros_client):
    assert validar(pasajeros_client, {}).status_code == 401
