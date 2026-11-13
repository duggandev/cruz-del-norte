# Cruz del Norte — servicios SC-01 a SC-06

Seis aplicaciones FastAPI independientes comparten una única base SQLite: `data/cruz_del_norte.db`.

| Servicio | Operaciones | Puerto |
|---|---|---:|
| SC-01 Disponibilidad de Viajes | `GET /api/v1/viajes/disponibilidad` | 8081 |
| SC-02 Gestión de Reservas | `POST /api/v1/reservas`, `POST /api/v1/reservas/{idReserva}/liberacion` | 8082 |
| SC-03 Validación de Pasajeros | `POST /api/v1/pasajeros/validaciones` | 8083 |
| SC-04 Gestión de Pagos | `POST /api/v1/pagos` | 8084 |
| SC-05 Emisión de Pasajes | `POST /api/v1/pasajes` | 8085 |
| SC-06 Planificación de Mantenimiento | `POST /api/v1/programaciones` | 8086 |

Los YAML oficiales mencionados en las especificaciones no estaban presentes en el repositorio recibido. Se conservaron las rutas, `operationId`, campos y códigos descritos en los documentos adjuntos. Antes del despliegue, los YAML oficiales deben compararse con el `/openapi.json` de cada servicio. Para la liberación de una reserva, cuyo cuerpo de respuesta no estaba detallado en el texto disponible, se adoptó el resultado mínimo `idReserva` y `estado`.

No se implementó lógica de SC-07, SC-08, SC-09 ni SC-10. La tabla `vehiculos` permanece como referencia de integración para la unidad comercial y SC-06.

## Instalación local

Requiere Python 3.11 o superior. En PowerShell:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Cambie `JWT_SECRET_KEY` en `.env` por un secreto aleatorio de al menos 32 bytes. `RESERVATION_TTL_MINUTES` controla la duración de las reservas temporales.

## Base de datos y migraciones

Los seis servicios leen el mismo `DATABASE_PATH`. SQLite se configura con claves foráneas, WAL, `busy_timeout=5000` y sincronización `NORMAL`.

```powershell
alembic upgrade head
python scripts\seed_dev.py
```

`python scripts\init_db.py` también ejecuta `alembic upgrade head`. El sembrado es idempotente y agrega el viaje, la reserva y el vehículo originales, además de 40 asientos para el viaje 1021. También agrega el viaje demostrativo 1022, Chimbote–Lima del 15 de diciembre de 2026, con 40 asientos.

Para cargar un conjunto académico grande y reproducible:

```powershell
python scripts\seed_bulk.py
```

El script agrega cientos de viajes, miles de asientos y reservas, pagos aprobados/rechazados, pasajes con PDF, vehículos y mantenimientos. Usa rangos reservados, es idempotente y solo se ejecuta en `academic_demo` o desarrollo.

Esquema compartido:

- `viajes` y `asientos_viaje`: oferta e inventario de SC-01.
- `reservas`: propiedad de SC-02 y consultada por SC-04/SC-05.
- `pagos`, `idempotencia_pagos`, `pasajes` y `programaciones_mantenimiento`.
- `vehiculos`: referencia externa compatible con SC-10, sin implementar ese servicio.

Un índice único parcial impide dos reservas `TEMPORAL`/`CONFIRMADA` para el mismo viaje y asiento. SC-02 actualiza temporales vencidas; SC-01 también deja de considerarlas bloqueantes inmediatamente.

## JWT de desarrollo

No se añadió un endpoint de autenticación:

```powershell
python scripts\generate_dev_token.py --roles ADMIN
```

Roles provisionales: `ADMIN`, `CAJA`, `EMISION` y `MANTENIMIENTO`.

## Ejecución local

En terminales separadas:

```powershell
uvicorn app.sc01_viajes.main:app --reload --port 8081
uvicorn app.sc02_reservas.main:app --reload --port 8082
uvicorn app.sc03_pasajeros.main:app --reload --port 8083
uvicorn app.sc04_pagos.main:app --reload --port 8084
uvicorn app.sc05_pasajes.main:app --reload --port 8085
uvicorn app.sc06_mantenimiento.main:app --reload --port 8086
```

También puede iniciar los seis procesos ocultos con:

```powershell
.\scripts\start_all.ps1
```

Swagger está en `http://localhost:PUERTO/docs`. Los PDF se sirven desde `http://localhost:8085/documentos/{codigo}.pdf`.

Para usar los contratos oficiales en Postman: seleccione **Import → Files**, cargue cada YAML y cree un entorno con las URL `http://localhost:8081` a `http://localhost:8086` y la variable `token`. Como los YAML no fueron entregados junto con este repositorio, no se generaron copias modificadas ni una colección que pudiera contradecirlos.

## Flujo de prueba

Use `Authorization: Bearer <TOKEN>` y `Content-Type: application/json` en operaciones con cuerpo.

1. Consulte `GET http://localhost:8081/api/v1/viajes/disponibilidad?origen=Lima&destino=Ica&fecha=2026-12-01`.
2. Valide el pasajero en SC-03. Mientras no exista proveedor oficial, la validación local responde 203 y nunca afirma consultar RENIEC.
3. Reserve un asiento disponible en SC-02:

```json
{"idViaje":1021,"idAsiento":13,"idCanal":1,"pasajero":{"dni":"45871236","nombres":"Ana","apellidos":"Rojas Vega"}}
```

4. Pague en SC-04 agregando una `Idempotency-Key` única:

```json
{"idReserva":5502,"importe":65.00,"medioPago":"EFECTIVO"}
```

5. Emita el pasaje en SC-05 con el `idTransaccion` recibido.

Con `PAYMENT_PROVIDER=mock` y `PAYMENT_MOCK_ENABLED=true`, PASARELA usa exclusivamente el simulador interno: `mock_aprobado`, `mock_rechazado`, `mock_pendiente`, `mock_error` y `mock_timeout`. No se realizan solicitudes HTTP ni se necesitan credenciales Culqi. El mock solo puede iniciarse en `academic_demo`, desarrollo o pruebas; en producción se rechaza. El canal de reserva 4 y el medio de pago TERCERO responden 501.

| `tokenPasarela` | Resultado | HTTP |
|---|---|---:|
| `mock_aprobado` | Pago `APROBADO` | 201 |
| `mock_rechazado` | Pago `RECHAZADO` | 201 |
| `mock_pendiente` | Pago `PENDIENTE` | 202 |
| `mock_error` | Error simulado de procesamiento | 502 |
| `mock_timeout` | Tiempo de espera simulado | 504 |

Las transacciones simuladas usan una secuencia protegida por la transacción SQLite: `MOCK-000001`, `MOCK-000002`, etc. Se registran con proveedor `MOCK_GATEWAY` y referencias `MOCK_REF-000001`, sin persistir el token ficticio. Para probar solo SC-04, importe `postman/Cruz_del_Norte_SC04_Mock.postman_collection.json`. Esta colección apunta al Gateway publicado, genera el JWT académico, crea su propia reserva y ejecuta 10 solicitudes con 26 aserciones para los cinco tokens mock y las reglas de idempotencia.

## Pruebas automatizadas

```powershell
pytest -q
```

Las pruebas usan una SQLite temporal que se elimina al terminar. Cubren cada servicio, bloqueos concurrentes e integración completa desde disponibilidad hasta el PDF.
