"""Esquema compartido inicial de SC-01, SC-02, SC-04, SC-05, SC-06 y SC-10."""
from alembic import op

from app.shared.database import Base
from app.shared import models  # noqa: F401

revision = "20261113_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # checkfirst preserva tablas de referencia que ya existan en una integración mayor.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
