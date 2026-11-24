"""snapshots by youtube_id

Revision ID: 991e478a6d7d
Revises: 4b3b64486d10
Create Date: 2026-11-24 03:58:25.322154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.db.types  # noqa: F401  (tipos propios en autogenerate)


# revision identifiers, used by Alembic.
revision: str = '991e478a6d7d'
down_revision: Union[str, Sequence[str], None] = '4b3b64486d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Snapshots independientes de la biblioteca (por youtube_id). Recrea la tabla copiando datos."""
    op.create_table(
        "metric_snapshots_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("youtube_id", sa.String(length=32), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=True),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reference_id"], ["references.id"],
                                name="fk_metric_snapshots_reference_id_references",
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_metric_snapshots"),
    )
    op.execute(
        """INSERT INTO metric_snapshots_new
           (id, youtube_id, reference_id, view_count, like_count, comment_count, captured_at)
           SELECT s.id, r.youtube_id, s.reference_id, s.view_count, s.like_count,
                  s.comment_count, s.captured_at
           FROM metric_snapshots s JOIN "references" r ON r.id = s.reference_id
           WHERE r.youtube_id IS NOT NULL"""
    )
    op.drop_table("metric_snapshots")
    op.rename_table("metric_snapshots_new", "metric_snapshots")
    for col in ("youtube_id", "reference_id", "captured_at"):
        op.create_index(f"ix_metric_snapshots_{col}", "metric_snapshots", [col])


def downgrade() -> None:
    op.create_table(
        "metric_snapshots_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=True),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reference_id"], ["references.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """INSERT INTO metric_snapshots_old
           SELECT id, reference_id, view_count, like_count, comment_count, captured_at
           FROM metric_snapshots WHERE reference_id IS NOT NULL"""
    )
    op.drop_table("metric_snapshots")
    op.rename_table("metric_snapshots_old", "metric_snapshots")
    op.create_index("ix_metric_snapshots_reference_id", "metric_snapshots", ["reference_id"])
