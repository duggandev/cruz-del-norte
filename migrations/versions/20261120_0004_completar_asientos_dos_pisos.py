"""Completa a 60 plazas los buses de dos pisos existentes."""
from alembic import op

revision = "20261120_0004"
down_revision = "20261120_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE viajes SET capacidad = 60 WHERE tipo_bus = 'DOS_PISOS_48'")
    op.execute("""
        INSERT INTO asientos_viaje (id_viaje, id_asiento, estado)
        SELECT v.id_viaje, s.numero, 'DISPONIBLE'
        FROM viajes v
        CROSS JOIN generate_series(49, 60) AS s(numero)
        WHERE v.tipo_bus = 'DOS_PISOS_48'
          AND NOT EXISTS (
              SELECT 1 FROM asientos_viaje a
              WHERE a.id_viaje = v.id_viaje AND a.id_asiento = s.numero
          )
    """)


def downgrade() -> None:
    op.execute("DELETE FROM asientos_viaje WHERE id_asiento BETWEEN 49 AND 60 AND id_viaje IN (SELECT id_viaje FROM viajes WHERE tipo_bus = 'DOS_PISOS_48')")
    op.execute("UPDATE viajes SET capacidad = 48 WHERE tipo_bus = 'DOS_PISOS_48'")
