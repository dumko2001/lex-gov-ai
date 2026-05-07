import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, DECIMAL, JSON
from app.core.database import Base

class Judgment(Base):
    __tablename__ = "judgments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ccms_case_id = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer)
    total_pages = Column(Integer, nullable=False)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="PENDING")
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    judgment_id = Column(String(36), ForeignKey("judgments.id"), nullable=False)
    status = Column(String(30), default="PENDING")
    iteration_count = Column(Integer, default=0)
    max_iterations = Column(Integer, default=3)
    pass1_prompt = Column(Text)
    pass1_raw_response = Column(Text)
    pass2_prompt = Column(Text)
    pass2_raw_response = Column(Text)
    sliced_text = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

class PageIndex(Base):
    __tablename__ = "page_indices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("processing_jobs.id"), nullable=False)
    judgment_id = Column(String(36), ForeignKey("judgments.id"), nullable=False)
    preamble_pages = Column(String(50))
    operative_pages = Column(String(50), nullable=False)
    breadcrumb_pages = Column(JSON)
    page_index_json = Column(JSON, nullable=False)
    correction_notes = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ActionPlan(Base):
    __tablename__ = "action_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("processing_jobs.id"), nullable=False)
    judgment_id = Column(String(36), ForeignKey("judgments.id"), nullable=False)
    case_id = Column(String(100))
    date_of_order = Column(DateTime(timezone=True), nullable=True)
    parties = Column(JSON)
    is_complete = Column(Boolean, default=False)
    overall_confidence = Column(DECIMAL(3, 2))
    raw_extraction_json = Column(JSON, nullable=False)
    sliced_text = Column(Text)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Directive(Base):
    __tablename__ = "directives"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_plan_id = Column(String(36), ForeignKey("action_plans.id"), nullable=False)
    judgment_id = Column(String(36), ForeignKey("judgments.id"), nullable=False)
    directive_number = Column(Integer, nullable=False)
    action_type = Column(String(20), nullable=False)
    responsible_dept = Column(String(50), nullable=False)
    deadline_explicit = Column(DateTime(timezone=True), nullable=True)
    deadline_inferred = Column(DateTime(timezone=True), nullable=True)
    source_page = Column(Integer)
    source_paragraph = Column(Text)
    source_text = Column(Text)
    confidence_score = Column(DECIMAL(3, 2))
    extracted_json = Column(JSON)
    status = Column(String(20), default="UNVERIFIED")
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True)
    department = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class VerificationAction(Base):
    __tablename__ = "verification_actions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    directive_id = Column(String(36), ForeignKey("directives.id"), nullable=False)
    action_plan_id = Column(String(36), ForeignKey("action_plans.id"), nullable=False)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action_type = Column(String(20), nullable=False)
    original_value = Column(JSON, nullable=False)
    edited_value = Column(JSON)
    correction_note = Column(Text)
    triggered_rerun = Column(Boolean, default=False)
    new_job_id = Column(String(36), ForeignKey("processing_jobs.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(36), nullable=False)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    old_state = Column(JSON)
    new_state = Column(JSON)
    extra_metadata = Column(JSON)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    judgment_id = Column(String(36), ForeignKey("judgments.id"), nullable=False)
    directive_id = Column(String(36), ForeignKey("directives.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    trigger_date = Column(DateTime(timezone=True), nullable=False)
    recipient_dept = Column(String(50), nullable=False)
    recipient_officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class FeedbackContext(Base):
    __tablename__ = "feedback_contexts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("processing_jobs.id"), nullable=False)
    iteration = Column(Integer, nullable=False)
    context_type = Column(String(20), nullable=False)
    feedback_note = Column(Text, nullable=False)
    appended_to_pass1 = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
