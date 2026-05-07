from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.all import Directive, Alert
from app.schemas.__init__ import DashboardResponse, DashboardSummary, DashboardDirective, AlertResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/", response_model=DashboardResponse)
def get_dashboard(department: str = "Revenue", db: Session = Depends(get_db)):
    """Get department dashboard with verified directives."""
    
    directives = db.query(Directive).filter(
        Directive.responsible_dept == department,
        Directive.status == "VERIFIED"
    ).order_by(Directive.deadline_inferred.asc().nullslast()).all()
    
    total = len(directives)
    urgent = 0
    upcoming = 0
    actioned = 0
    
    dashboard_directives = []
    for d in directives:
        days_remaining = None
        if d.deadline_inferred:
            days_remaining = (d.deadline_inferred - datetime.now(timezone.utc)).days
            if days_remaining < 0:
                actioned += 1  # Actually this logic should check status = ACTIONED
            elif days_remaining <= 10:
                urgent += 1
            elif days_remaining <= 30:
                upcoming += 1
        
        dashboard_directives.append(DashboardDirective(
            id=d.id,
            case_id=d.action_plan.case_id if d.action_plan else "",
            judgment_id=d.judgment_id,
            directive_number=d.directive_number,
            action_type=d.action_type,
            responsible_dept=d.responsible_dept,
            deadline_explicit=d.deadline_explicit,
            deadline_inferred=d.deadline_inferred,
            days_remaining=days_remaining,
            status=d.status,
            source_page=d.source_page
        ))
    
    return DashboardResponse(
        summary=DashboardSummary(
            total=total,
            urgent=urgent,
            upcoming=upcoming,
            actioned=actioned
        ),
        directives=dashboard_directives
    )

@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(department: str = "Revenue", unread_only: bool = False, db: Session = Depends(get_db)):
    """Get alerts for a department."""
    query = db.query(Alert).filter(Alert.recipient_dept == department)
    if unread_only:
        query = query.filter(Alert.is_read == False)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    return alerts

@router.post("/alerts/mark-read")
def mark_alerts_read(alert_ids: list[str], db: Session = Depends(get_db)):
    """Mark alerts as read."""
    db.query(Alert).filter(Alert.id.in_(alert_ids)).update({"is_read": True})
    db.commit()
    return {"message": "Alerts marked as read"}
