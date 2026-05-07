"""init

Revision ID: 001_init
Revises: 
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("employee_id", sa.String(50), unique=True),
        sa.Column("department", sa.String(50), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "judgments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("ccms_case_id", sa.String(50), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer()),
        sa.Column("total_pages", sa.Integer(), nullable=False),
        sa.Column("upload_date", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("judgment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("judgments.id"), nullable=False),
        sa.Column("status", sa.String(30), default="PENDING"),
        sa.Column("iteration_count", sa.Integer(), default=0),
        sa.Column("max_iterations", sa.Integer(), default=3),
        sa.Column("pass1_prompt", sa.Text()),
        sa.Column("pass1_raw_response", sa.Text()),
        sa.Column("pass2_prompt", sa.Text()),
        sa.Column("pass2_raw_response", sa.Text()),
        sa.Column("sliced_text", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "page_indices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id"), nullable=False),
        sa.Column("judgment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("judgments.id"), nullable=False),
        sa.Column("preamble_pages", sa.String(50)),
        sa.Column("operative_pages", sa.String(50), nullable=False),
        sa.Column("breadcrumb_pages", postgresql.ARRAY(sa.String())),
        sa.Column("page_index_json", postgresql.JSONB(), nullable=False),
        sa.Column("correction_notes", postgresql.ARRAY(sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "action_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id"), nullable=False),
        sa.Column("judgment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("judgments.id"), nullable=False),
        sa.Column("case_id", sa.String(100)),
        sa.Column("date_of_order", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parties", postgresql.JSONB()),
        sa.Column("is_complete", sa.Boolean(), default=False),
        sa.Column("overall_confidence", sa.DECIMAL(3, 2)),
        sa.Column("raw_extraction_json", postgresql.JSONB(), nullable=False),
        sa.Column("sliced_text", sa.Text()),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "directives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("action_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_plans.id"), nullable=False),
        sa.Column("judgment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("judgments.id"), nullable=False),
        sa.Column("directive_number", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("responsible_dept", sa.String(50), nullable=False),
        sa.Column("deadline_explicit", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_inferred", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_page", sa.Integer()),
        sa.Column("source_paragraph", sa.Text()),
        sa.Column("source_text", sa.Text()),
        sa.Column("confidence_score", sa.DECIMAL(3, 2)),
        sa.Column("extracted_json", postgresql.JSONB()),
        sa.Column("status", sa.String(20), default="UNVERIFIED"),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "verification_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("directive_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("directives.id"), nullable=False),
        sa.Column("action_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_plans.id"), nullable=False),
        sa.Column("officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("original_value", postgresql.JSONB(), nullable=False),
        sa.Column("edited_value", postgresql.JSONB()),
        sa.Column("correction_note", sa.Text()),
        sa.Column("triggered_rerun", sa.Boolean(), default=False),
        sa.Column("new_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("old_state", postgresql.JSONB()),
        sa.Column("new_state", postgresql.JSONB()),
        sa.Column("extra_metadata", postgresql.JSONB()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("judgment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("judgments.id"), nullable=False),
        sa.Column("directive_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("directives.id"), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("trigger_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recipient_dept", sa.String(50), nullable=False),
        sa.Column("recipient_officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "feedback_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processing_jobs.id"), nullable=False),
        sa.Column("iteration", sa.Integer(), nullable=False),
        sa.Column("context_type", sa.String(20), nullable=False),
        sa.Column("feedback_note", sa.Text(), nullable=False),
        sa.Column("appended_to_pass1", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("feedback_contexts")
    op.drop_table("alerts")
    op.drop_table("audit_log")
    op.drop_table("verification_actions")
    op.drop_table("directives")
    op.drop_table("action_plans")
    op.drop_table("page_indices")
    op.drop_table("processing_jobs")
    op.drop_table("judgments")
    op.drop_table("users")
