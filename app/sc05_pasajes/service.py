import secrets
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.sc05_pasajes import repository
from app.sc05_pasajes.schemas import PasajeRequest
from app.shared.config import settings
from app.shared.errors import ApiError
from app.shared.models import Pasaje


LIMA = ZoneInfo("America/Lima")


def _codigo(now: datetime) -> str:
    return f"CDN-{now.year}-{secrets.randbelow(1_000_000):06d}"


def _crear_pdf(path: Path, codigo: str, reserva, viaje, pago) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    width, height = A4
    pdf.setTitle(f"Pasaje {codigo}")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(25 * mm, height - 25 * mm, "CRUZ DEL NORTE")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(25 * mm, height - 38 * mm, f"Pasaje: {codigo}")
    lines = [
        ("Pasajero", f"{reserva.pasajero_nombres} {reserva.pasajero_apellidos}"),
        ("DNI", reserva.pasajero_dni),
        ("Origen", viaje.origen),
        ("Destino", viaje.destino),
        ("Fecha del viaje", viaje.fecha.isoformat()),
        ("Hora de salida", viaje.hora_salida),
        ("Asiento", str(reserva.id_asiento)),
        ("Importe", f"S/ {Decimal(pago.importe_centavos) / 100:.2f}"),
        ("Transacción", pago.id_transaccion),
    ]
    y = height - 55 * mm
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(25 * mm, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(65 * mm, y, value)
        y -= 9 * mm
    pdf.line(25 * mm, y, width - 25 * mm, y)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(25 * mm, y - 8 * mm, "Documento emitido electrónicamente por Cruz del Norte.")
    pdf.save()


def emitir_pasaje(db: Session, data: PasajeRequest) -> tuple[dict, Path]:
    pdf_path: Path | None = None
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        row = repository.get_reserva_con_viaje(db, data.id_reserva)
        if not row:
            raise ApiError(404, "No encontramos la reserva solicitada.")
        reserva, viaje = row
        existing = repository.get_pasaje(db, data.id_reserva)
        if existing:
            raise ApiError(409, "La reserva ya tiene un pasaje emitido.")
        pago = repository.get_pago(db, data.id_transaccion)
        if not pago:
            raise ApiError(422, "No existe un pago confirmado con esa transacción.")
        if pago.id_reserva != data.id_reserva:
            raise ApiError(422, "La transacción no corresponde a la reserva indicada.")
        if pago.estado != "APROBADO":
            raise ApiError(422, "El pago no está aprobado.")

        now = datetime.now(LIMA)
        for _ in range(10):
            codigo = _codigo(now)
            pdf_path = settings.pasajes_directory / f"{codigo}.pdf"
            if not pdf_path.exists():
                break
        else:
            raise ApiError(500, "No fue posible generar un código único de pasaje.")
        url = f"{settings.public_pasajes_url.rstrip('/')}/{codigo}.pdf"
        pasaje = Pasaje(
            codigo=codigo,
            id_reserva=data.id_reserva,
            id_pago=pago.id_pago,
            estado="EMITIDO",
            fecha_emision=now,
            documento_url=url,
            documento_path=str(pdf_path),
        )
        db.add(pasaje)
        db.flush()
        _crear_pdf(pdf_path, codigo, reserva, viaje, pago)
        db.commit()
        return {
            "codigo": codigo,
            "idReserva": data.id_reserva,
            "estado": "EMITIDO",
            "fechaEmision": now.isoformat(),
            "documentoUrl": url,
        }, pdf_path
    except ApiError:
        db.rollback()
        raise
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        if pdf_path and pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
        if isinstance(exc, IntegrityError):
            raise ApiError(409, "El pasaje entra en conflicto con una emisión existente.") from exc
        raise ApiError(503, "La base de datos está temporalmente ocupada.") from exc
    except Exception:
        db.rollback()
        if pdf_path and pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
        raise
