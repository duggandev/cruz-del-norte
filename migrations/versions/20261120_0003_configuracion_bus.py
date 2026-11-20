"""Agrega configuración física del bus a cada viaje."""
from alembic import op
import sqlalchemy as sa

revision = "20261120_0003"
down_revision = "20261113_0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("viajes", sa.Column("tipo_bus", sa.String(length=30), nullable=False, server_default="DOS_PISOS_48"))
    op.add_column("viajes", sa.Column("pisos", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("viajes", sa.Column("capacidad", sa.Integer(), nullable=False, server_default="48"))
    op.execute("UPDATE viajes SET capacidad = 60 WHERE tipo_bus = 'DOS_PISOS_48'")

def downgrade() -> None:
    op.drop_column("viajes", "capacidad")
    op.drop_column("viajes", "pisos")
    op.drop_column("viajes", "tipo_bus")
