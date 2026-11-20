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
    viajes = connection.execute(text("SELECT id_viaje FROM viajes WHERE tipo_bus = :tipo"), {"tipo": "DOS_PISOS_48"}).scalars().all()
    for id_viaje in viajes:
        for id_asiento in range(49, 61):
            connection.execute(text("""
                INSERT INTO asientos_viaje (id_viaje, id_asiento, estado)
                VALUES (:id_viaje, :id_asiento, 'DISPONIBLE')
                ON CONFLICT (id_viaje, id_asiento) DO NOTHING
            """), {"id_viaje": id_viaje, "id_asiento": id_asiento})


def downgrade() -> None:
    op.execute("DELETE FROM asientos_viaje WHERE id_asiento BETWEEN 49 AND 60 AND id_viaje IN (SELECT id_viaje FROM viajes WHERE tipo_bus = 'DOS_PISOS_48')")
    op.execute("UPDATE viajes SET capacidad = 48 WHERE tipo_bus = 'DOS_PISOS_48'")
