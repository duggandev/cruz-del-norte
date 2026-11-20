"""Completa a 60 plazas los buses de dos pisos existentes."""
from alembic import op
from sqlalchemy import text

revision = "20261120_0004"
down_revision = "20261120_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(text("UPDATE viajes SET capacidad = 60 WHERE tipo_bus = :tipo"), {"tipo": "DOS_PISOS_48"})


def downgrade() -> None:
    op.execute("UPDATE viajes SET capacidad = 48 WHERE tipo_bus = 'DOS_PISOS_48'")
