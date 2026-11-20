"""Agrega configuración física del bus a cada viaje."""
from alembic import op

revision = "20261120_0003"
down_revision = "20261113_0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE viajes ADD COLUMN IF NOT EXISTS tipo_bus VARCHAR(30) NOT NULL DEFAULT 'DOS_PISOS_48'")
    op.execute("ALTER TABLE viajes ADD COLUMN IF NOT EXISTS pisos INTEGER NOT NULL DEFAULT 2")
    op.execute("ALTER TABLE viajes ADD COLUMN IF NOT EXISTS capacidad INTEGER NOT NULL DEFAULT 48")
    op.execute("UPDATE viajes SET capacidad = 60 WHERE tipo_bus = 'DOS_PISOS_48'")

def downgrade() -> None:
    op.execute("ALTER TABLE viajes DROP COLUMN IF EXISTS capacidad")
    op.execute("ALTER TABLE viajes DROP COLUMN IF EXISTS pisos")
    op.execute("ALTER TABLE viajes DROP COLUMN IF EXISTS tipo_bus")
