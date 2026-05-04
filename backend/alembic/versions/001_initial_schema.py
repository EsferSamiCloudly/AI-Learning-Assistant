"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS app")
    op.execute("CREATE SCHEMA IF NOT EXISTS vectors")

    # auth.users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )

    # auth.refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text, unique=True, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )

    # app.documents
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("embed_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # app.chat_sessions
    op.create_table(
        "chat_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("app.documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.Text, nullable=False, server_default="general"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # app.chat_messages
    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("app.chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="check_role"),
        schema="app",
    )

    # app.essay_outputs
    op.create_table(
        "essay_outputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.Text, nullable=False),
        sa.Column("tone", sa.Text, nullable=False),
        sa.Column("length", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # app.question_sets
    op.create_table(
        "question_sets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("difficulty", sa.Text, nullable=False),
        sa.Column("domain", sa.Text, nullable=True),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("questions", JSONB, nullable=False),
        sa.Column("source_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # app.evaluation_results
    op.create_table(
        "evaluation_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_set_id", UUID(as_uuid=True), sa.ForeignKey("app.question_sets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.Text, nullable=False),
        sa.Column("results", JSONB, nullable=False),
        sa.Column("total_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # app.summarization_outputs
    op.create_table(
        "summarization_outputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("app.documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", sa.Text, nullable=False),
        sa.Column("mode", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="app",
    )

    # vectors.document_chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("app.documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text, nullable=False),  # stored as vector(384) via raw SQL below
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        schema="vectors",
    )

    # Change embedding column to proper vector type and add index
    op.execute("ALTER TABLE vectors.document_chunks ALTER COLUMN embedding TYPE vector(384) USING embedding::vector")
    op.execute("CREATE INDEX ON vectors.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vectors.document_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS app.summarization_outputs CASCADE")
    op.execute("DROP TABLE IF EXISTS app.evaluation_results CASCADE")
    op.execute("DROP TABLE IF EXISTS app.question_sets CASCADE")
    op.execute("DROP TABLE IF EXISTS app.essay_outputs CASCADE")
    op.execute("DROP TABLE IF EXISTS app.chat_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS app.chat_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS app.documents CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.refresh_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.users CASCADE")
    op.execute("DROP SCHEMA IF EXISTS vectors CASCADE")
    op.execute("DROP SCHEMA IF EXISTS app CASCADE")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")