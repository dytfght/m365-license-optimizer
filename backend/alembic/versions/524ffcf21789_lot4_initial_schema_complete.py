"""lot4_initial_schema_complete

Revision ID: 524ffcf21789
Revises:
Create Date: 2025-11-23 23:55:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "524ffcf21789"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in optimizer schema with full safety checks"""

    # 1. CRÉATION SÉCURISÉE DU SCHÉMA
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS optimizer"))

    # NOTE : On ne crée pas les ENUMs manuellement ici via op.execute.
    # SQLAlchemy va détecter les sa.Enum() dans les create_table ci-dessous
    # et générer les CREATE TYPE automatiquement.

    # 3. Tables
    # Table: tenant_clients
    op.create_table(
        "tenant_clients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
            comment="Azure AD Tenant ID",
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "country", sa.String(length=2), nullable=False, comment="ISO 3166-1 alpha-2"
        ),
        sa.Column(
            "default_language",
            sa.String(length=5),
            nullable=False,
            server_default="fr-FR",
        ),
        # SQLAlchemy crée le type 'onboarding_status' ici :
        sa.Column(
            "onboarding_status",
            sa.Enum(
                "pending",
                "active",
                "suspended",
                "error",
                name="onboarding_status",
                schema="optimizer",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("csp_customer_id", sa.String(length=36), nullable=True),
        sa.Column(
            "metadatas",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="optimizer",
    )
    op.create_index(
        "ix_tenant_clients_tenant_id",
        "tenant_clients",
        ["tenant_id"],
        unique=True,
        schema="optimizer",
    )

    # Table: tenant_app_registrations
    op.create_table(
        "tenant_app_registrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("client_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("certificate_thumbprint", sa.String(length=64), nullable=True),
        sa.Column(
            "authority_url",
            sa.String(length=255),
            nullable=False,
            server_default="https://login.microsoftonline.com/common",
        ),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        # SQLAlchemy crée le type 'consent_status' ici :
        sa.Column(
            "consent_status",
            sa.Enum(
                "pending",
                "granted",
                "revoked",
                "expired",
                name="consent_status",
                schema="optimizer",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("consent_granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_client_id"], ["optimizer.tenant_clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="optimizer",
    )
    op.create_index(
        "ix_tenant_app_registrations_tenant_client_id",
        "tenant_app_registrations",
        ["tenant_client_id"],
        unique=True,
        schema="optimizer",
    )

    # Table: users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("graph_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_principal_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "account_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("office_location", sa.String(length=255), nullable=True),
        sa.Column(
            "member_of_groups",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_client_id"], ["optimizer.tenant_clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="optimizer",
    )
    op.create_index(
        "ix_users_graph_id", "users", ["graph_id"], unique=True, schema="optimizer"
    )
    op.create_index(
        "ix_users_tenant_client_id",
        "users",
        ["tenant_client_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_users_user_principal_name",
        "users",
        ["user_principal_name"],
        unique=False,
        schema="optimizer",
    )

    # Table: license_assignments
    op.create_table(
        "license_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_date", sa.DateTime(timezone=True), nullable=True),
        # SQLAlchemy crée le type 'license_status' ici :
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "suspended",
                "disabled",
                "trial",
                name="license_status",
                schema="optimizer",
            ),
            nullable=False,
            server_default="active",
        ),
        # SQLAlchemy crée le type 'assignment_source' ici :
        sa.Column(
            "source",
            sa.Enum(
                "manual",
                "auto",
                "group_policy",
                name="assignment_source",
                schema="optimizer",
            ),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["optimizer.users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sku_id", name="uq_user_sku"),
        schema="optimizer",
    )
    op.create_index(
        "ix_license_assignments_sku_id",
        "license_assignments",
        ["sku_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_license_assignments_user_id",
        "license_assignments",
        ["user_id"],
        unique=False,
        schema="optimizer",
    )

    # Table: usage_metrics
    op.create_table(
        "usage_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("last_seen_date", sa.Date(), nullable=True),
        sa.Column(
            "email_activity",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "onedrive_activity",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "sharepoint_activity",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "teams_activity",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "office_web_activity",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "office_desktop_activated",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "storage_used_bytes", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "mailbox_size_bytes", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["optimizer.users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "period", "report_date", name="uq_user_period_date"
        ),
        schema="optimizer",
    )
    op.create_index(
        "ix_usage_metrics_report_date",
        "usage_metrics",
        ["report_date"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_usage_metrics_user_id",
        "usage_metrics",
        ["user_id"],
        unique=False,
        schema="optimizer",
    )


def downgrade() -> None:
    """Drop all tables and types, and finally the schema"""
    # Suppression dans l'ordre inverse
    op.drop_table("usage_metrics", schema="optimizer")
    op.drop_table("license_assignments", schema="optimizer")
    op.drop_table("users", schema="optimizer")
    op.drop_table("tenant_app_registrations", schema="optimizer")
    op.drop_table("tenant_clients", schema="optimizer")

    # Dans le downgrade, nous devons supprimer les types manuellement car drop_table ne le fait pas toujours
    op.execute("DROP TYPE IF EXISTS optimizer.assignment_source")
    op.execute("DROP TYPE IF EXISTS optimizer.license_status")
    op.execute("DROP TYPE IF EXISTS optimizer.consent_status")
    op.execute("DROP TYPE IF EXISTS optimizer.onboarding_status")

    # Nettoyage final du schéma
    op.execute(sa.text("DROP SCHEMA IF EXISTS optimizer CASCADE"))
