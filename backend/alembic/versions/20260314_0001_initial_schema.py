"""Initial schema."""

from alembic import op

from common.core.database import Base, import_models


revision = "20260314_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    import_models()
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    import_models()
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
