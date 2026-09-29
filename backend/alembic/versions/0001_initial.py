"""Initial iProcurement schema.

This first migration uses SQLAlchemy metadata so the SQLite demo and PostgreSQL
deployment create the same application schema. Later migrations can be normal
Alembic diffs.
"""
from alembic import op
from app.models.entities import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
