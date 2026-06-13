"""Initial schema — matches init.sql.

Revision ID: 001
Revises: None
Create Date: 2026-06-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Signals ──────────────────────────────────────────────────────
    op.create_table(
        "signals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("platform", sa.Text, nullable=True),
        sa.Column("community", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("author", sa.Text, nullable=True),
        sa.Column("category", sa.Text, nullable=True),
        sa.Column("confidence", sa.REAL, server_default="0.0"),
        sa.Column(
            "ingested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_signals_source", "signals", ["source"])
    op.create_index("idx_signals_platform", "signals", ["platform"])
    op.create_index("idx_signals_category", "signals", ["category"])
    op.create_index("idx_signals_ingested_at", "signals", [sa.text("ingested_at DESC")])

    # ── Deployments ──────────────────────────────────────────────────
    op.create_table(
        "deployments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.Text, nullable=True),
        sa.Column(
            "deployment_id",
            sa.UUID,
            nullable=False,
            unique=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("platform", sa.Text, nullable=False),
        sa.Column("community", sa.Text, nullable=True),
        sa.Column("account_id", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("autonomy_level", sa.Text, nullable=False, server_default="'L1'"),
        sa.Column("status", sa.Text, nullable=False, server_default="'pending'"),
        sa.Column("deployed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("metrics", sa.JSON, server_default=sa.text("'{}'::jsonb")),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_deployments_client", "deployments", ["client_id"])
    op.create_index("idx_deployments_platform", "deployments", ["platform"])
    op.create_index("idx_deployments_status", "deployments", ["status"])
    op.execute(
        "CREATE INDEX idx_deployments_embedding ON deployments USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ── Accounts ─────────────────────────────────────────────────────
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("platform", sa.Text, nullable=False),
        sa.Column("username", sa.Text, nullable=False),
        sa.Column("credentials", sa.JSON, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text, nullable=False, server_default="'maturing'"),
        sa.Column("karma", sa.Integer, server_default="0"),
        sa.Column("age_days", sa.Integer, server_default="0"),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("subreddits", sa.ARRAY(sa.Text), server_default="{}"),
        sa.Column("metadata", sa.JSON, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_accounts_platform", "accounts", ["platform"])
    op.create_index("idx_accounts_status", "accounts", ["status"])
    op.create_unique_index("idx_accounts_platform_username", "accounts", ["platform", "username"])

    # ── Clients ──────────────────────────────────────────────────────
    op.create_table(
        "clients",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("voice_profile", sa.JSON, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("constraints", sa.JSON, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text, nullable=False, server_default="'active'"),
        sa.Column(
            "onboarded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("metadata", sa.JSON, server_default=sa.text("'{}'::jsonb")),
    )

    # ── Semantic Memory ──────────────────────────────────────────────
    op.create_table(
        "semantic_memory",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("pattern", sa.Text, nullable=False),
        sa.Column("evidence_ids", sa.ARRAY(sa.BigInteger), server_default="{}"),
        sa.Column("client_ids", sa.ARRAY(sa.Text), server_default="{}"),
        sa.Column("confidence", sa.REAL, server_default="0.0"),
        sa.Column("reinforced_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_semantic_memory_confidence", "semantic_memory", [sa.text("confidence DESC")]
    )

    # ── Audit Log ────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("target_type", sa.Text, nullable=True),
        sa.Column("target_id", sa.Text, nullable=True),
        sa.Column("details", sa.JSON, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_audit_log_actor", "audit_log", ["actor"])
    op.create_index("idx_audit_log_timestamp", "audit_log", [sa.text("timestamp DESC")])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("semantic_memory")
    op.drop_table("clients")
    op.drop_table("accounts")
    op.drop_table("deployments")
    op.drop_table("signals")
    op.execute("DROP EXTENSION IF EXISTS vector")
