from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base


def utc_now() -> datetime:
    return datetime.now().astimezone()


class Viaje(Base):
    __tablename__ = "viajes"
    id_viaje: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origen: Mapped[str] = mapped_column(String(120), nullable=False)
    destino: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_salida: Mapped[str] = mapped_column(String(5), nullable=False)
    tarifa_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo_bus: Mapped[str] = mapped_column(String(30), nullable=False, default="DOS_PISOS_48", server_default="DOS_PISOS_48")
    pisos: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2")
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False, default=48, server_default="48")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AsientoViaje(Base):
    __tablename__ = "asientos_viaje"
    __table_args__ = (
        CheckConstraint("estado IN ('DISPONIBLE','NO_DISPONIBLE')", name="ck_asientos_viaje_estado"),
    )
    id_viaje: Mapped[int] = mapped_column(ForeignKey("viajes.id_viaje", ondelete="CASCADE"), primary_key=True)
    id_asiento: Mapped[int] = mapped_column(Integer, primary_key=True)
    estado: Mapped[str] = mapped_column(String(20), default="DISPONIBLE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint("estado IN ('TEMPORAL','CONFIRMADA','VENCIDA','CANCELADA')", name="ck_reservas_estado"),
        CheckConstraint("id_canal IN (1,2,3,4)", name="ck_reservas_canal"),
        Index(
            "uq_reserva_asiento_bloqueado",
            "id_viaje",
            "id_asiento",
            unique=True,
            sqlite_where=text("estado IN ('TEMPORAL','CONFIRMADA')"),
            postgresql_where=text("estado IN ('TEMPORAL','CONFIRMADA')"),
        ),
    )
    id_reserva: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_viaje: Mapped[int] = mapped_column(ForeignKey("viajes.id_viaje"), nullable=False, index=True)
    id_asiento: Mapped[int] = mapped_column(Integer, nullable=False)
    id_canal: Mapped[int] = mapped_column(Integer, nullable=False)
    pasajero_dni: Mapped[str] = mapped_column(String(20), nullable=False)
    pasajero_nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    pasajero_apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    vencimiento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    viaje: Mapped[Viaje] = relationship()


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    __table_args__ = (CheckConstraint("estado IN ('DISPONIBLE','NO_DISPONIBLE','FUERA_DE_SERVICIO')", name="ck_vehiculos_estado"),)
    id_vehiculo: Mapped[int] = mapped_column(Integer, primary_key=True)
    placa: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint("medio_pago IN ('EFECTIVO','POS','PASARELA','TERCERO')", name="ck_pagos_medio"),
        CheckConstraint("estado IN ('APROBADO','RECHAZADO','PENDIENTE')", name="ck_pagos_estado"),
        CheckConstraint("importe_centavos > 0", name="ck_pagos_importe"),
        Index("uq_pago_aprobado_reserva", "id_reserva", unique=True, sqlite_where=text("estado = 'APROBADO'"), postgresql_where=text("estado = 'APROBADO'")),
    )
    id_pago: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_transaccion: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    id_reserva: Mapped[int] = mapped_column(ForeignKey("reservas.id_reserva"), nullable=False, index=True)
    importe_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    medio_pago: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    referencia_pos: Mapped[str | None] = mapped_column(String(120))
    proveedor: Mapped[str | None] = mapped_column(String(50))
    referencia_proveedor: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class IdempotenciaPago(Base):
    __tablename__ = "idempotencia_pagos"
    idempotency_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    id_pago: Mapped[int | None] = mapped_column(ForeignKey("pagos.id_pago"))
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Pasaje(Base):
    __tablename__ = "pasajes"
    __table_args__ = (CheckConstraint("estado IN ('EMITIDO','ANULADO')", name="ck_pasajes_estado"),)
    id_pasaje: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    id_reserva: Mapped[int] = mapped_column(ForeignKey("reservas.id_reserva"), unique=True, nullable=False)
    id_pago: Mapped[int] = mapped_column(ForeignKey("pagos.id_pago"), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    documento_url: Mapped[str] = mapped_column(String(500), nullable=False)
    documento_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProgramacionMantenimiento(Base):
    __tablename__ = "programaciones_mantenimiento"
    __table_args__ = (
        CheckConstraint("kilometraje >= 0", name="ck_programacion_kilometraje"),
        CheckConstraint("tipo IN ('PREVENTIVO','CORRECTIVO')", name="ck_programacion_tipo"),
        CheckConstraint("estado IN ('PROGRAMADO','CANCELADO')", name="ck_programacion_estado"),
        Index("uq_programacion_activa", "id_vehiculo", "fecha", unique=True, sqlite_where=text("estado = 'PROGRAMADO'"), postgresql_where=text("estado = 'PROGRAMADO'")),
    )
    id_programacion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    id_vehiculo: Mapped[int] = mapped_column(ForeignKey("vehiculos.id_vehiculo"), nullable=False, index=True)
    kilometraje: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
