import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.sc04_pagos import repository
from app.sc04_pagos.providers import get_payment_provider
from app.sc04_pagos.providers.base import (
    PaymentProviderRequest,
    PaymentProviderResult,
    ProviderConfigurationError,
    ProviderProcessingError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from app.sc04_pagos.schemas import MedioPago, PagoRequest
from app.shared.errors import ApiError
from app.shared.models import IdempotenciaPago, Pago


def _centavos(importe: Decimal) -> int:
    return int((importe * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _hash_request(data: PagoRequest) -> str:
    canonical = {
        "idReserva": data.id_reserva,
        "importeCentavos": _centavos(data.importe),
        "medioPago": data.medio_pago.value,
        "tokenPasarela": data.token_pasarela,
        "referenciaPos": data.referencia_pos,
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _response(pago: Pago) -> dict:
    return {
        "idTransaccion": pago.id_transaccion,
        "idReserva": pago.id_reserva,
        "importe": float(Decimal(pago.importe_centavos) / 100),
        "estado": pago.estado,
    }


def _procesar_proveedor(
    data: PagoRequest,
    importe_centavos: int,
    idempotency_key: str,
    transaction_sequence: int | None = None,
) -> PaymentProviderResult:
    if data.medio_pago == MedioPago.EFECTIVO:
        transaction = f"efc_{uuid.uuid4().hex[:20]}"
        return PaymentProviderResult("APROBADO", transaction, "INTERNO", transaction)
    if data.medio_pago == MedioPago.TERCERO:
        raise ApiError(501, "El procesamiento mediante terceros aún no está implementado.")
    if data.medio_pago == MedioPago.POS:
        raise ApiError(503, "El adaptador POS no está disponible en la demostración académica.")
    try:
        return get_payment_provider().process(
            PaymentProviderRequest(
                id_reserva=data.id_reserva,
                importe_centavos=importe_centavos,
                token=data.token_pasarela or "",
                idempotency_key=idempotency_key,
                transaction_sequence=transaction_sequence,
            )
        )
    except ProviderValidationError as exc:
        raise ApiError(422, str(exc)) from exc
    except ProviderConfigurationError as exc:
        raise ApiError(503, str(exc)) from exc
    except ProviderProcessingError as exc:
        raise ApiError(502, str(exc)) from exc
    except ProviderTimeoutError as exc:
        raise ApiError(504, str(exc)) from exc


def procesar_pago(db: Session, data: PagoRequest, key: str) -> tuple[dict, int]:
    if not key.strip() or len(key) > 200:
        raise ApiError(400, "Idempotency-Key es obligatorio y debe tener hasta 200 caracteres.")
    request_hash = _hash_request(data)
    try:
        db.execute(text("BEGIN IMMEDIATE" if db.bind.dialect.name == "sqlite" else "BEGIN"))
        previous = repository.get_idempotencia(db, key)
        if previous:
            if previous.request_hash != request_hash:
                raise ApiError(409, "La Idempotency-Key ya fue utilizada con datos diferentes.")
            if previous.response_json and previous.response_status:
                return json.loads(previous.response_json), previous.response_status
            raise ApiError(409, "La solicitud con esta Idempotency-Key está siendo procesada.")

        idem = IdempotenciaPago(idempotency_key=key, request_hash=request_hash)
        db.add(idem)
        db.flush()

        row = repository.get_reserva_con_viaje(db, data.id_reserva)
        if not row:
            raise ApiError(404, "No encontramos la reserva solicitada.")
        reserva, viaje = row
        now = datetime.now(timezone.utc)
        vencimiento = reserva.vencimiento
        if vencimiento.tzinfo is None:
            vencimiento = vencimiento.replace(tzinfo=ZoneInfo("America/Lima"))
        if reserva.estado == "CANCELADA":
            raise ApiError(409, "La reserva está cancelada.")
        if reserva.estado == "VENCIDA" or vencimiento <= now:
            if reserva.estado == "TEMPORAL":
                reserva.estado = "VENCIDA"
            raise ApiError(410, "La reserva ha vencido.")
        importe_centavos = _centavos(data.importe)
        if importe_centavos != viaje.tarifa_centavos:
            raise ApiError(422, "El importe no coincide con la tarifa del viaje.")
        if repository.get_pago_aprobado(db, data.id_reserva):
            raise ApiError(409, "La reserva ya tiene un pago aprobado.")

        mock_sequence = repository.get_next_mock_sequence(db) if data.medio_pago == MedioPago.PASARELA else None
        result = _procesar_proveedor(data, importe_centavos, key, mock_sequence)
        pago = Pago(
            id_transaccion=result.id_transaccion,
            id_reserva=data.id_reserva,
            importe_centavos=importe_centavos,
            medio_pago=data.medio_pago.value,
            estado=result.estado,
            referencia_pos=data.referencia_pos,
            proveedor=result.proveedor,
            referencia_proveedor=result.referencia_proveedor,
        )
        db.add(pago)
        db.flush()
        if result.estado == "APROBADO":
            reserva.estado = "CONFIRMADA"
        body = _response(pago)
        status_code = 202 if result.estado == "PENDIENTE" else 201
        idem.id_pago = pago.id_pago
        idem.response_status = status_code
        idem.response_json = json.dumps(body, separators=(",", ":"))
        db.commit()
        return body, status_code
    except ApiError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "El pago entra en conflicto con una operación existente.") from exc
    except OperationalError as exc:
        db.rollback()
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc
