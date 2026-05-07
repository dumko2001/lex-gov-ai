from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

# ─── User Schemas ───
class UserBase(BaseModel):
    email: str
    full_name: str
    employee_id: Optional[str] = None
    department: str
    role: str = Field(..., pattern="^(NODAL_OFFICER|DEPT_HEAD|LAW_DEPT|ADMIN)$")

class UserCreate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Judgment Schemas ───
class JudgmentBase(BaseModel):
    ccms_case_id: str
    file_name: str
    total_pages: int

class JudgmentCreate(JudgmentBase):
    pass

class JudgmentResponse(JudgmentBase):
    id: UUID
    file_path: str
    file_size_bytes: Optional[int]
    upload_date: datetime
    status: str
    uploaded_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

class JudgmentListResponse(BaseModel):
    id: UUID
    ccms_case_id: str
    file_name: str
    status: str
    upload_date: datetime

    class Config:
        from_attributes = True

# ─── Processing Job Schemas ───
class ProcessingJobResponse(BaseModel):
    id: UUID
    judgment_id: UUID
    status: str
    iteration_count: int
    max_iterations: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: UUID
    judgment_id: UUID
    status: str
    iteration_count: int
    progress: str

# ─── Page Index Schemas ───
class PageIndexResponse(BaseModel):
    id: UUID
    job_id: UUID
    preamble_pages: Optional[str]
    operative_pages: str
    breadcrumb_pages: Optional[List[str]]
    page_index_json: dict
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Directive Schemas ───
class DirectiveBase(BaseModel):
    directive_number: int
    action_type: str = Field(..., pattern="^(COMPLY|CONSIDER_APPEAL)$")
    responsible_dept: str
    deadline_explicit: Optional[datetime]
    deadline_inferred: Optional[datetime]
    source_page: Optional[int]
    source_paragraph: Optional[str]
    source_text: Optional[str]
    confidence_score: Optional[float]

class DirectiveCreate(DirectiveBase):
    action_plan_id: UUID
    judgment_id: UUID
    extracted_json: dict

class DirectiveResponse(DirectiveBase):
    id: UUID
    action_plan_id: UUID
    judgment_id: UUID
    status: str
    verified_by: Optional[UUID]
    verified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class DirectiveEditRequest(BaseModel):
    action_type: Optional[str] = None
    responsible_dept: Optional[str] = None
    deadline_explicit: Optional[datetime] = None
    deadline_inferred: Optional[datetime] = None
    edit_reason: str

class DirectiveRedoRequest(BaseModel):
    correction_note: str

# ─── Action Plan Schemas ───
class ActionPlanResponse(BaseModel):
    id: UUID
    job_id: UUID
    judgment_id: UUID
    case_id: Optional[str]
    date_of_order: Optional[datetime]
    parties: Optional[dict]
    is_complete: bool
    overall_confidence: Optional[float]
    status: str
    directives: List[DirectiveResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Verification Schemas ───
class VerificationActionRequest(BaseModel):
    action_type: str = Field(..., pattern="^(APPROVE|EDIT|REDO)$")
    edited_value: Optional[dict] = None
    correction_note: Optional[str] = None

class VerificationActionResponse(BaseModel):
    id: UUID
    directive_id: UUID
    action_type: str
    original_value: dict
    edited_value: Optional[dict]
    correction_note: Optional[str]
    triggered_rerun: bool
    new_job_id: Optional[UUID]
    timestamp: datetime

    class Config:
        from_attributes = True

# ─── Dashboard Schemas ───
class DashboardSummary(BaseModel):
    total: int
    urgent: int
    upcoming: int
    actioned: int

class DashboardDirective(BaseModel):
    id: UUID
    case_id: str
    judgment_id: UUID
    directive_number: int
    action_type: str
    responsible_dept: str
    deadline_explicit: Optional[datetime]
    deadline_inferred: Optional[datetime]
    days_remaining: Optional[int]
    status: str
    source_page: Optional[int]

    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    summary: DashboardSummary
    directives: List[DashboardDirective]

# ─── Alert Schemas ───
class AlertResponse(BaseModel):
    id: UUID
    judgment_id: UUID
    directive_id: Optional[UUID]
    alert_type: str
    trigger_date: datetime
    recipient_dept: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertMarkReadRequest(BaseModel):
    alert_ids: List[UUID]

# ─── Auth Schemas ───
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ─── Pipeline Trigger ───
class PipelineTriggerResponse(BaseModel):
    job_id: UUID
    judgment_id: UUID
    status: str
    message: str
