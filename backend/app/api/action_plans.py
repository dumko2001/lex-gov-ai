from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.all import (
    ActionPlan,
    Directive,
    VerificationAction,
    FeedbackContext,
    ProcessingJob,
    Judgment,
    User,
)
from app.schemas.__init__ import (
    ActionPlanResponse,
    VerificationActionRequest,
    VerificationActionResponse,
    DirectiveEditRequest,
    DirectiveRedoRequest,
)
from app.services.pipeline_service import pipeline_service

router = APIRouter(prefix="/action-plans", tags=["action-plans"])


@router.get("/{action_plan_id}", response_model=ActionPlanResponse)
def get_action_plan(action_plan_id: str, db: Session = Depends(get_db)):
    """Get action plan with all directives."""
    plan = db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
    if not plan:
        raise HTTPException(404, "Action plan not found")

    directives = (
        db.query(Directive).filter(Directive.action_plan_id == action_plan_id).all()
    )

    # Manually build response
    from app.schemas.__init__ import DirectiveResponse

    response = ActionPlanResponse(
        id=plan.id,
        job_id=plan.job_id,
        judgment_id=plan.judgment_id,
        case_id=plan.case_id,
        date_of_order=plan.date_of_order,
        parties=plan.parties,
        is_complete=plan.is_complete,
        overall_confidence=(
            float(plan.overall_confidence) if plan.overall_confidence else None
        ),
        status=plan.status,
        directives=[
            DirectiveResponse(
                id=d.id,
                action_plan_id=d.action_plan_id,
                judgment_id=d.judgment_id,
                directive_number=d.directive_number,
                action_type=d.action_type,
                responsible_dept=d.responsible_dept,
                deadline_explicit=d.deadline_explicit,
                deadline_inferred=d.deadline_inferred,
                source_page=d.source_page,
                source_paragraph=d.source_paragraph,
                source_text=d.source_text,
                confidence_score=(
                    float(d.confidence_score) if d.confidence_score else None
                ),
                status=d.status,
                verified_by=d.verified_by,
                verified_at=d.verified_at,
                created_at=d.created_at,
            )
            for d in directives
        ],
        created_at=plan.created_at,
    )
    return response


@router.get("/judgment/{judgment_id}", response_model=ActionPlanResponse)
def get_action_plan_by_judgment(judgment_id: str, db: Session = Depends(get_db)):
    """Get the latest action plan for a judgment."""
    plan = (
        db.query(ActionPlan)
        .filter(ActionPlan.judgment_id == judgment_id)
        .order_by(ActionPlan.created_at.desc())
        .first()
    )

    if not plan:
        raise HTTPException(404, "No action plan found for this judgment")

    return get_action_plan(str(plan.id), db)


@router.post(
    "/{action_plan_id}/directives/{directive_id}/verify",
    response_model=VerificationActionResponse,
)
def verify_directive(
    action_plan_id: str,
    directive_id: str,
    request: VerificationActionRequest,
    db: Session = Depends(get_db),
):
    """Officer verifies a directive: Approve, Edit, or Redo."""

    directive = (
        db.query(Directive)
        .filter(
            Directive.id == directive_id, Directive.action_plan_id == action_plan_id
        )
        .first()
    )

    if not directive:
        raise HTTPException(404, "Directive not found")

    # Get current values as original
    original_value = {
        "action_type": directive.action_type,
        "responsible_dept": directive.responsible_dept,
        "deadline_explicit": (
            str(directive.deadline_explicit) if directive.deadline_explicit else None
        ),
        "deadline_inferred": (
            str(directive.deadline_inferred) if directive.deadline_inferred else None
        ),
    }

    triggered_rerun = False
    new_job_id = None
    officer = (
        db.query(User)
        .filter(User.role == "ADMIN")
        .order_by(User.created_at.asc())
        .first()
        or db.query(User).order_by(User.created_at.asc()).first()
    )
    officer_id = str(directive.verified_by or (officer.id if officer else ""))

    if request.action_type == "APPROVE":
        directive.status = "VERIFIED"
        if officer_id:
            directive.verified_by = officer_id
        directive.verified_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )

    elif request.action_type == "EDIT":
        if not request.edited_value:
            raise HTTPException(400, "Edited value required for EDIT action")

        # Apply edits
        if "action_type" in request.edited_value:
            directive.action_type = request.edited_value["action_type"]
        if "responsible_dept" in request.edited_value:
            directive.responsible_dept = request.edited_value["responsible_dept"]
        if "deadline_explicit" in request.edited_value:
            from datetime import datetime

            directive.deadline_explicit = (
                datetime.strptime(request.edited_value["deadline_explicit"], "%Y-%m-%d")
                if request.edited_value["deadline_explicit"]
                else None
            )
        if "deadline_inferred" in request.edited_value:
            from datetime import datetime

            directive.deadline_inferred = (
                datetime.strptime(request.edited_value["deadline_inferred"], "%Y-%m-%d")
                if request.edited_value["deadline_inferred"]
                else None
            )

        directive.status = "VERIFIED"
        if officer_id:
            directive.verified_by = officer_id
        directive.verified_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )

    elif request.action_type == "REDO":
        if not request.correction_note:
            raise HTTPException(400, "Correction note required for REDO action")

        triggered_rerun = True

        # Create feedback context
        feedback = FeedbackContext(
            job_id=directive.action_plan.job_id,
            iteration=1,
            context_type="OFFICER_REDO",
            feedback_note=request.correction_note,
        )
        db.add(feedback)
        db.flush()

        # Create new processing job and trigger rerun
        new_job = ProcessingJob(
            judgment_id=directive.judgment_id,
            status="PENDING",
            iteration_count=0,
            max_iterations=3,
        )
        db.add(new_job)
        db.flush()
        new_job_id = new_job.id

        # We'll trigger the actual rerun asynchronously
        # For prototype, we return immediately with new_job_id

    db.flush()

    # Create verification action record
    action = VerificationAction(
        directive_id=directive.id,
        action_plan_id=action_plan_id,
        officer_id=officer_id,
        action_type=request.action_type,
        original_value=original_value,
        edited_value=request.edited_value if request.edited_value else None,
        correction_note=request.correction_note,
        triggered_rerun=triggered_rerun,
        new_job_id=new_job_id,
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    return VerificationActionResponse(
        id=action.id,
        directive_id=action.directive_id,
        action_type=action.action_type,
        original_value=action.original_value,
        edited_value=action.edited_value,
        correction_note=action.correction_note,
        triggered_rerun=action.triggered_rerun,
        new_job_id=action.new_job_id,
        timestamp=action.timestamp,
    )


@router.post("/{action_plan_id}/publish")
def publish_action_plan(action_plan_id: str, db: Session = Depends(get_db)):
    """Publish verified action plan to department dashboard."""
    plan = db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
    if not plan:
        raise HTTPException(404, "Action plan not found")

    # Check all directives are verified
    unverified = (
        db.query(Directive)
        .filter(
            Directive.action_plan_id == action_plan_id, Directive.status != "VERIFIED"
        )
        .count()
    )

    if unverified > 0:
        raise HTTPException(
            400, f"Cannot publish: {unverified} directive(s) still unverified"
        )

    plan.status = "PUBLISHED"

    # Update judgment status
    judgment = db.query(Judgment).filter(Judgment.id == plan.judgment_id).first()
    if judgment:
        judgment.status = "VERIFIED"

    db.commit()
    return {"message": "Action plan published to dashboard"}
