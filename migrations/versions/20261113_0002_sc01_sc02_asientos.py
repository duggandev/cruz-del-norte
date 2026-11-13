"""Añade inventario de asientos y bloqueo único de reservas activas."""
from alembic import op
from sqlalchemy import inspect, text

from app.shared.models import AsientoViaje


revision = "20261113_0002"
down_revision = "20261113_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    AsientoViaje.__table__.create(bind=bind, checkfirst=True)
    indexes = {item["name"] for item in inspect(bind).get_indexes("reservas")}
    if "uq_reserva_asiento_bloqueado" not in indexes:
        bind.execute(text(
            "CREATE UNIQUE INDEX uq_reserva_asiento_bloqueado "
            "ON reservas (id_viaje, id_asiento) "
            "WHERE estado IN ('TEMPORAL','CONFIRMADA')"
        ))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("DROP INDEX IF EXISTS uq_reserva_asiento_bloqueado"))
    AsientoViaje.__table__.drop(bind=bind, checkfirst=True)
