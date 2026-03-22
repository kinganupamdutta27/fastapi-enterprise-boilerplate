"""Create items table.

Revision ID: 001
Revises:
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS items (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name        VARCHAR(255)    NOT NULL,
            description TEXT,
            created_at  TIMESTAMPTZ     NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ     NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_items_created_at ON items (created_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS items;")
