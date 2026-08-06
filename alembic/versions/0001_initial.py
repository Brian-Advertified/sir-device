"""Initial Sir Device schema without seed data."""

from alembic import op

from app.infrastructure.db.base import Base
import app.infrastructure.db.models  # noqa: F401


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
