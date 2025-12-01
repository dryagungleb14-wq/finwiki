from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20251201_0001"
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not table_exists("qa_pairs"):
        op.create_table(
            "qa_pairs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("question", sa.String, nullable=False),
            sa.Column("answer", sa.String, nullable=False),
            sa.Column("question_processed", sa.String, nullable=True),
            sa.Column("answer_processed", sa.String, nullable=True),
            sa.Column(
                "status",
                sa.Enum(
                    "pending",
                    "approved",
                    "rejected",
                    "unanswered",
                    name="qapairstatus",
                ),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("submitted_by", sa.String, nullable=True),
            sa.Column("slack_user", sa.String, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not table_exists("keywords"):
        op.create_table(
            "keywords",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("qa_pair_id", sa.Integer, sa.ForeignKey("qa_pairs.id"), nullable=False),
            sa.Column("keyword", sa.String, nullable=False),
        )

    if not table_exists("questions"):
        op.create_table(
            "questions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("text", sa.String, nullable=False),
            sa.Column("source", sa.String, nullable=True),
            sa.Column("external_id", sa.String, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not table_exists("answers"):
        op.create_table(
            "answers",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("question_id", sa.Integer, sa.ForeignKey("questions.id"), nullable=False),
            sa.Column("text", sa.String, nullable=False),
            sa.Column("source", sa.String, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    if table_exists("answers"):
        op.drop_table("answers")
    if table_exists("questions"):
        op.drop_table("questions")
    if table_exists("keywords"):
        op.drop_table("keywords")
    if table_exists("qa_pairs"):
        op.drop_table("qa_pairs")


