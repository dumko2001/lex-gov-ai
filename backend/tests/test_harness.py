import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pipeline_service import pipeline_service
from app.services.pdf_service import pdf_service
from app.services.alert_engine import alert_engine
from app.models.all import Judgment, PageIndex, ActionPlan, Directive


class TestParsePageRange:
    def test_single_range(self):
        assert pipeline_service._parse_page_range("45-52") == [45, 46, 47, 48, 49, 50, 51, 52]

    def test_comma_separated(self):
        assert pipeline_service._parse_page_range("1,3,5") == [1, 3, 5]

    def test_mixed(self):
        assert pipeline_service._parse_page_range("10-12,15") == [10, 11, 12, 15]


class TestPipelineWithMocks:
    @pytest.mark.asyncio
    async def test_full_pipeline_creates_action_plan(self):
        db = MagicMock()
        judgment = Judgment(
            id=uuid.uuid4(),
            ccms_case_id="CCMS/2024/001",
            file_name="test.pdf",
            file_path="/uploads/test.pdf",
            total_pages=50,
            status="PENDING",
        )
        db.query.return_value.filter.return_value.first.return_value = judgment

        with patch("app.services.pipeline_service.sarvam_client") as mock_sarvam, \
             patch("app.services.pipeline_service.pdf_service") as mock_pdf:
            page_rows = [(i, "Procedural history") for i in range(1, 48)]
            page_rows.extend([
                (48, "Respondents are directed that compliance must be completed within 30 days."),
                (49, "Accordingly, order is passed and respondents are directed to file their report."),
                (50, "Disposed of. Sd/- Judge."),
            ])
            mock_pdf.extract_text_by_page.return_value = page_rows

            mock_sarvam.extract_action_plan = AsyncMock(return_value={
                "case_id": "CCMS/2024/001",
                "date_of_order": "2024-01-15",
                "parties": {"petitioner": "A", "respondent": "B"},
                "directives": [
                    {
                        "action_type": "COMPLY",
                        "responsible_dept": "Revenue",
                        "deadline_explicit": "2024-02-15",
                        "deadline_inferred": None,
                        "source_page": 48,
                        "source_paragraph": "Para 10",
                        "source_text": "The respondent shall comply within 30 days.",
                        "confidence_score": 0.95,
                    }
                ],
                "is_complete_info_present": True,
                "overall_confidence": 0.92,
            })

            mock_pdf.get_page_images.return_value = [b"img1", b"img2"]
            mock_pdf.slice_pdf.return_value = "/uploads/test_sliced.pdf"
            mock_pdf.extract_text.return_value = "Operative text here"

            job = await pipeline_service.run_pipeline(db, str(judgment.id))

            assert job.status == "NEEDS_REVIEW"
            assert job.iteration_count == 0

            # Verify PageIndex was created with correct operative range
            page_index_calls = [c for c in db.add.call_args_list if isinstance(c.args[0], PageIndex)]
            assert len(page_index_calls) == 1
            page_index = page_index_calls[0].args[0]
            assert page_index.operative_pages == "48-50"

            # Verify ActionPlan was created
            plan_calls = [c for c in db.add.call_args_list if isinstance(c.args[0], ActionPlan)]
            assert len(plan_calls) == 1
            plan = plan_calls[0].args[0]
            assert plan.case_id == "CCMS/2024/001"
            assert plan.is_complete is True

            # Verify Directive was created
            directive_calls = [c for c in db.add.call_args_list if isinstance(c.args[0], Directive)]
            assert len(directive_calls) == 1
            directive = directive_calls[0].args[0]
            assert directive.action_type == "COMPLY"
            assert directive.responsible_dept == "Revenue"
            assert directive.status == "UNVERIFIED"
            assert directive.deadline_explicit is not None

            mock_pdf.slice_pdf.assert_called_once_with("/uploads/test.pdf", [48, 49, 50])

    @pytest.mark.asyncio
    async def test_self_correction_loop(self):
        db = MagicMock()
        judgment = Judgment(
            id=uuid.uuid4(),
            ccms_case_id="CCMS/2024/002",
            file_name="test2.pdf",
            file_path="/uploads/test2.pdf",
            total_pages=60,
            status="PENDING",
        )
        db.query.return_value.filter.return_value.first.return_value = judgment

        with patch("app.services.pipeline_service.sarvam_client") as mock_sarvam, \
             patch("app.services.pipeline_service.pdf_service") as mock_pdf:
            page_rows = [(i, "Procedural history") for i in range(1, 55)]
            page_rows.extend([
                (55, "Respondents are directed that the action shall be completed within 30 days."),
                (56, "Accordingly, this petition is disposed of."),
                (57, "Sd/- Judge."),
                (58, "Procedural text."),
                (59, "Procedural text."),
                (60, "Procedural text."),
            ])
            mock_pdf.extract_text_by_page.return_value = page_rows

            first_extraction = {
                "case_id": "CCMS/2024/002",
                "date_of_order": "2024-02-01",
                "parties": {"petitioner": "X", "respondent": "Y"},
                "directives": [
                    {
                        "action_type": "COMPLY",
                        "responsible_dept": "Home",
                        "deadline_explicit": "2024-03-01",
                        "deadline_inferred": None,
                        "source_page": 55,
                        "source_paragraph": "Para 5",
                        "source_text": "Respondent shall process within 30 days.",
                        "confidence_score": 0.88,
                    }
                ],
                "is_complete_info_present": False,
                "overall_confidence": 0.70,
            }
            second_extraction = {
                "case_id": "CCMS/2024/002",
                "date_of_order": "2024-02-01",
                "parties": {"petitioner": "X", "respondent": "Y"},
                "directives": [
                    {
                        "action_type": "COMPLY",
                        "responsible_dept": "Home",
                        "deadline_explicit": "2024-03-01",
                        "deadline_inferred": None,
                        "source_page": 55,
                        "source_paragraph": "Para 5",
                        "source_text": "Respondent shall process within 30 days.",
                        "confidence_score": 0.92,
                    }
                ],
                "is_complete_info_present": True,
                "overall_confidence": 0.92,
            }
            mock_sarvam.extract_action_plan = AsyncMock(side_effect=[first_extraction, second_extraction])

            mock_pdf.get_page_images.return_value = [b"img"]
            mock_pdf.slice_pdf.return_value = "/uploads/test2_sliced.pdf"
            mock_pdf.extract_text.return_value = "Operative text"

            job = await pipeline_service.run_pipeline(db, str(judgment.id))

            assert job.status == "NEEDS_REVIEW"
            assert job.iteration_count == 1
            assert mock_sarvam.extract_action_plan.await_count == 2


class TestPDFSlicing:
    def test_slice_pdf_produces_correct_pages(self, tmp_path):
        pytest.importorskip("reportlab")
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "multi_page.pdf"
        c = canvas.Canvas(str(pdf_path))
        for i in range(1, 6):
            c.drawString(100, 700, f"Page {i}")
            c.showPage()
        c.save()

        sliced_path = pdf_service.slice_pdf(str(pdf_path), [2, 4])
        assert sliced_path.endswith("_sliced.pdf")

        from pypdf import PdfReader
        reader = PdfReader(sliced_path)
        assert len(reader.pages) == 2


class TestAlertEngine:
    def test_generates_compliance_and_appeal_alerts(self):
        db = MagicMock()
        judgment = MagicMock()
        judgment.id = uuid.uuid4()
        judgment.ccms_case_id = "CCMS/001"
        judgment.upload_date = datetime.now(timezone.utc)
        judgment.status = "PENDING"

        directive1 = MagicMock()
        directive1.id = uuid.uuid4()
        directive1.directive_number = 1
        directive1.action_type = "COMPLY"
        directive1.responsible_dept = "Revenue"
        directive1.deadline_inferred = datetime.now(timezone.utc) + timedelta(days=5)
        directive1.status = "UNVERIFIED"

        directive2 = MagicMock()
        directive2.id = uuid.uuid4()
        directive2.directive_number = 2
        directive2.action_type = "CONSIDER_APPEAL"
        directive2.responsible_dept = "Law"
        directive2.deadline_inferred = datetime.now(timezone.utc) + timedelta(days=10)
        directive2.status = "UNVERIFIED"

        db.query.return_value.filter.return_value.first.return_value = judgment
        # We need to handle two different filter chains; using side_effect
        def query_side_effect(model):
            m = MagicMock()
            if model == Judgment:
                m.filter.return_value.first.return_value = judgment
            elif model == Directive:
                m.filter.return_value.all.return_value = [directive1, directive2]
            return m

        db.query.side_effect = query_side_effect

        alerts = alert_engine.generate_alerts(db, str(judgment.id))

        alert_types = [a.alert_type for a in alerts]
        assert "COMPLIANCE_DEADLINE_10_DAYS" in alert_types
        assert "APPEAL_DEADLINE_15_DAYS" in alert_types


def _make_db():
    """Return a MagicMock session that simulates auto-incrementing IDs on flush/commit."""
    db = MagicMock()
    _added = []

    def mock_add(obj):
        _added.append(obj)

    def _assign_ids():
        for obj in _added:
            if hasattr(obj, "id") and getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            if hasattr(obj, "timestamp") and getattr(obj, "timestamp", None) is None:
                obj.timestamp = datetime.now(timezone.utc)
            if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)

    db.add = MagicMock(side_effect=mock_add)
    db.commit = MagicMock(side_effect=_assign_ids)
    db.flush = MagicMock(side_effect=_assign_ids)
    db.refresh = MagicMock()
    return db


class TestVerificationActions:
    def test_approve_directive(self):
        from app.api.action_plans import verify_directive
        from app.schemas import VerificationActionRequest

        db = _make_db()
        directive = MagicMock()
        directive.id = uuid.uuid4()
        directive.action_plan_id = uuid.uuid4()
        directive.action_type = "COMPLY"
        directive.responsible_dept = "Revenue"
        directive.deadline_explicit = None
        directive.deadline_inferred = None
        directive.status = "UNVERIFIED"
        directive.verified_by = None
        directive.judgment_id = uuid.uuid4()
        directive.action_plan = MagicMock()
        directive.action_plan.job_id = uuid.uuid4()

        db.query.return_value.filter.return_value.first.return_value = directive

        request = VerificationActionRequest(action_type="APPROVE")
        response = verify_directive(str(directive.action_plan_id), str(directive.id), request, db)

        assert response.action_type == "APPROVE"
        assert directive.status == "VERIFIED"
        assert response.triggered_rerun is False

    def test_edit_directive(self):
        from app.api.action_plans import verify_directive
        from app.schemas import VerificationActionRequest

        db = _make_db()
        directive = MagicMock()
        directive.id = uuid.uuid4()
        directive.action_plan_id = uuid.uuid4()
        directive.action_type = "COMPLY"
        directive.responsible_dept = "Revenue"
        directive.deadline_explicit = None
        directive.deadline_inferred = None
        directive.status = "UNVERIFIED"
        directive.verified_by = None
        directive.judgment_id = uuid.uuid4()
        directive.action_plan = MagicMock()
        directive.action_plan.job_id = uuid.uuid4()

        db.query.return_value.filter.return_value.first.return_value = directive

        request = VerificationActionRequest(
            action_type="EDIT",
            edited_value={"responsible_dept": "Home", "deadline_explicit": "2024-12-31"}
        )
        response = verify_directive(str(directive.action_plan_id), str(directive.id), request, db)

        assert response.action_type == "EDIT"
        assert directive.responsible_dept == "Home"
        assert directive.deadline_explicit is not None
        assert directive.status == "VERIFIED"

    def test_redo_directive(self):
        from app.api.action_plans import verify_directive
        from app.schemas import VerificationActionRequest

        db = _make_db()
        directive = MagicMock()
        directive.id = uuid.uuid4()
        directive.action_plan_id = uuid.uuid4()
        directive.action_type = "COMPLY"
        directive.responsible_dept = "Revenue"
        directive.deadline_explicit = None
        directive.deadline_inferred = None
        directive.status = "UNVERIFIED"
        directive.verified_by = None
        directive.judgment_id = uuid.uuid4()
        directive.action_plan = MagicMock()
        directive.action_plan.job_id = uuid.uuid4()

        db.query.return_value.filter.return_value.first.return_value = directive

        request = VerificationActionRequest(
            action_type="REDO",
            correction_note="Missed conditional directive"
        )
        response = verify_directive(str(directive.action_plan_id), str(directive.id), request, db)

        assert response.action_type == "REDO"
        assert response.triggered_rerun is True
        assert response.new_job_id is not None
