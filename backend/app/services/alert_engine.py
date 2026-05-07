import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.all import Directive, Alert, Judgment

logger = logging.getLogger(__name__)


def _now():
    """Return current UTC datetime, naive (for SQLite compatibility)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _days_until(dt):
    """Safe days calculation handling naive/aware mix."""
    if dt is None:
        return None
    now = _now()
    # If dt is aware, make it naive
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return (dt - now).days


class AlertEngine:
    """Generate alerts based on directive deadlines and verification status."""

    def generate_alerts(self, db: Session, judgment_id: str) -> list:
        """Generate alerts for a judgment after pipeline completion."""
        alerts = []

        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        if not judgment:
            return alerts

        directives = (
            db.query(Directive)
            .filter(
                Directive.judgment_id == judgment_id,
                Directive.status.in_(["UNVERIFIED", "PENDING_VERIFICATION"]),
            )
            .all()
        )

        now = _now()

        for directive in directives:
            # Alert: Compliance deadline approaching (< 10 days)
            if directive.deadline_inferred:
                days_remaining = _days_until(directive.deadline_inferred)

                if days_remaining < 0 and directive.status != "ACTIONED":
                    alerts.append(
                        Alert(
                            judgment_id=judgment_id,
                            directive_id=directive.id,
                            alert_type="COMPLIANCE_OVERDUE",
                            trigger_date=now,
                            recipient_dept=directive.responsible_dept,
                            message=f"Compliance deadline passed for Case {judgment.ccms_case_id}. Directive #{directive.directive_number}.",
                        )
                    )
                elif (
                    days_remaining <= 10
                    and days_remaining >= 0
                    and directive.status == "UNVERIFIED"
                ):
                    alerts.append(
                        Alert(
                            judgment_id=judgment_id,
                            directive_id=directive.id,
                            alert_type="COMPLIANCE_DEADLINE_10_DAYS",
                            trigger_date=now,
                            recipient_dept=directive.responsible_dept,
                            message=f"Compliance deadline in {days_remaining} days for Case {judgment.ccms_case_id}. Directive #{directive.directive_number}.",
                        )
                    )

            # Alert: Appeal deadline approaching
            if (
                directive.action_type == "CONSIDER_APPEAL"
                and directive.deadline_inferred
            ):
                days_remaining = _days_until(directive.deadline_inferred)
                if (
                    days_remaining <= 15
                    and days_remaining >= 0
                    and directive.status == "UNVERIFIED"
                ):
                    alerts.append(
                        Alert(
                            judgment_id=judgment_id,
                            directive_id=directive.id,
                            alert_type="APPEAL_DEADLINE_15_DAYS",
                            trigger_date=now,
                            recipient_dept="Law",
                            message=f"Appeal window closes in {days_remaining} days for Case {judgment.ccms_case_id}.",
                        )
                    )

        # Alert: No verified plan within 7 days of upload
        upload_date = judgment.upload_date
        if upload_date and upload_date.tzinfo is not None:
            upload_date = upload_date.replace(tzinfo=None)
        days_since_upload = (now - upload_date).days if upload_date else 0
        if days_since_upload >= 7 and judgment.status in ["PENDING", "PROCESSING"]:
            alerts.append(
                Alert(
                    judgment_id=judgment_id,
                    alert_type="NO_PLAN_7_DAYS",
                    trigger_date=now,
                    recipient_dept="Admin",
                    message=f"No verified action plan for Case {judgment.ccms_case_id} after 7 days.",
                )
            )

        for alert in alerts:
            db.add(alert)

        db.commit()
        return alerts


alert_engine = AlertEngine()
