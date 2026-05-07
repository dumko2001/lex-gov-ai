import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.all import (
    Judgment, ProcessingJob, PageIndex, ActionPlan, Directive, 
    FeedbackContext
)
from app.services.pdf_service import pdf_service
from app.services.sarvam_vision_client import sarvam_vision_client
from app.services.sarvam_client import sarvam_client

settings = get_settings()
logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self):
        self.max_iterations = settings.MAX_ITERATIONS
    
    async def run_pipeline(
        self, 
        db: Session, 
        judgment_id: str,
        correction_notes: Optional[List[str]] = None,
        previous_job_id: Optional[str] = None
    ) -> ProcessingJob:
        """Run the full two-pass pipeline on a judgment."""
        
        judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
        if not judgment:
            raise ValueError(f"Judgment {judgment_id} not found")
        
        job = ProcessingJob(
            judgment_id=judgment.id,
            status="PASS1_RUNNING",
            iteration_count=0,
            max_iterations=self.max_iterations
        )
        db.add(job)
        db.flush()
        # Persist the job row before long-running AI work so async failures stay visible.
        db.commit()
        db.refresh(job)
        
        try:
            # === PASS 1: Structural Mapping ===
            logger.info(f"Job {job.id}: Starting Pass 1 (local structural mapping)")
            page_index = await self._run_pass1(
                db, job, judgment, correction_notes or []
            )
            
            if not page_index or not page_index.operative_pages:
                raise ValueError("Pass 1 failed: no operative pages identified")
            
            job.status = "PASS1_COMPLETE"
            db.flush()
            
            # === PDF SLICING ===
            operative_page_list = self._parse_page_range(page_index.operative_pages)
            sliced_path = pdf_service.slice_pdf(judgment.file_path, operative_page_list)
            sliced_text = pdf_service.extract_text(sliced_path)
            job.sliced_text = sliced_text[:50000]
            db.flush()
            
            job.status = "SLICING_COMPLETE"
            db.flush()
            
            # === PASS 2: Extraction & Reasoning (Sarvam-105B) ===
            logger.info(f"Job {job.id}: Starting Pass 2 (Sarvam-105B Extraction)")
            action_plan = await self._run_pass2(
                db, job, judgment, sliced_text, page_index.operative_pages
            )
            
            job.status = "PASS2_COMPLETE"
            db.flush()
            
            # === SELF-CORRECTION LOOP ===
            if not action_plan.is_complete and job.iteration_count < self.max_iterations:
                logger.info(f"Job {job.id}: Self-correction iteration {job.iteration_count + 1}")
                
                # Generate correction note from Pass 2 assessment
                correction_note = action_plan.raw_extraction_json.get(
                    "completeness_assessment", 
                    "Extraction may be incomplete. Please re-scan for missed directives."
                )
                
                feedback = FeedbackContext(
                    job_id=job.id,
                    iteration=job.iteration_count + 1,
                    context_type="MODEL_SELF_CORRECTION",
                    feedback_note=correction_note
                )
                db.add(feedback)
                db.flush()
                
                job.iteration_count += 1
                job.status = "SELF_CORRECTION_LOOP"
                db.flush()
                
                # Re-run Pass 1 with correction note
                page_index = await self._run_pass1(db, job, judgment, [correction_note])
                
                # Re-slice and re-extract
                operative_page_list = self._parse_page_range(page_index.operative_pages)
                sliced_path = pdf_service.slice_pdf(judgment.file_path, operative_page_list)
                sliced_text = pdf_service.extract_text(sliced_path)
                
                action_plan = await self._run_pass2(
                    db, job, judgment, sliced_text, page_index.operative_pages
                )
            
            job.status = "NEEDS_REVIEW"
            action_plan.status = "NEEDS_REVIEW"
            job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.flush()
            
            judgment.status = "NEEDS_REVIEW"
            db.flush()
            
            logger.info(f"Job {job.id}: Pipeline complete. Status: {job.status}")
            return job
            
        except Exception as e:
            logger.error(f"Job {job.id}: Pipeline failed: {e}")
            db.rollback()
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job.id).first()
            judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
            job.status = "FAILED"
            job.error_message = str(e)
            if judgment:
                judgment.status = "FAILED"
            db.commit()
            raise
    
    async def _run_pass1(self, db: Session, job: ProcessingJob, judgment: Judgment, correction_notes: List[str]) -> PageIndex:
        """Run Pass 1: Extract text with pdfplumber, identify operative pages via heuristics."""

        # Extract text page-by-page using pdfplumber
        pages = pdf_service.extract_text_by_page(judgment.file_path)
        page_texts = {num: text for num, text in pages}

        # Score each page
        classifications = []
        for page_num in range(1, judgment.total_pages + 1):
            text = page_texts.get(page_num, "")
            scores = self._score_page(text)
            classifications.append({
                "page": page_num,
                "operative_score": scores["operative"],
                "preamble_score": scores["preamble"],
                "procedural_score": scores["procedural"],
            })

        # Find operative block: work backwards from end
        operative_pages = self._find_operative_block(classifications, judgment.total_pages)

        # Find preamble: work forwards from start
        preamble_pages = self._find_preamble_block(classifications)

        # Build ranges
        if operative_pages:
            operative_range = self._build_page_range(operative_pages)
        else:
            # Fallback: last 5 pages
            operative_range = f"{max(1, judgment.total_pages - 4)}-{judgment.total_pages}"

        preamble_range = self._build_page_range(preamble_pages) if preamble_pages else "1-2"

        # Store a preview of Pass 1
        preview_lines = [f"Page {c['page']}: op={c['operative_score']} pre={c['preamble_score']} pro={c['procedural_score']}" for c in classifications]
        job.pass1_raw_response = "\n".join(preview_lines[:50])
        db.flush()

        page_index = PageIndex(
            job_id=job.id,
            judgment_id=judgment.id,
            preamble_pages=preamble_range,
            operative_pages=operative_range,
            breadcrumb_pages=[],
            page_index_json={"classifications": classifications},
            correction_notes=correction_notes if correction_notes else []
        )
        db.add(page_index)
        db.flush()

        return page_index
    
    def _parse_vision_output(self, markdown: str, total_pages: int) -> List[Dict[str, Any]]:
        """Parse Sarvam Vision markdown output to classify pages."""
        classifications = []
        
        # Split by page markers (Sarvam Vision includes page markers like "<!-- PAGES 1-10 -->")
        page_markers = re.findall(r'<!--\s*PAGES?\s+(\d+)(?:-(\d+))?\s*-->', markdown)
        
        if not page_markers:
            # No page markers, try to infer from content
            # Split by common page break patterns
            sections = re.split(r'\n\s*-+\s*\n|\n\s*#{3,}\s*\n', markdown)
            pages_per_section = max(1, total_pages // max(len(sections), 1))
            
            current_page = 1
            for section in sections:
                if current_page > total_pages:
                    break
                
                category = self._classify_section(section)
                for p in range(current_page, min(current_page + pages_per_section, total_pages + 1)):
                    classifications.append({"page": p, "category": category, "confidence": 0.8})
                
                current_page += pages_per_section
        else:
            # Parse using page markers
            for start, end in page_markers:
                start_page = int(start)
                end_page = int(end) if end else start_page
                
                # Extract content between this marker and the next
                pattern = rf'<!--\s*PAGES?\s+{start}(?:-{end})?\s*-->(.*?)(?=<!--\s*PAGES?\s+\d+|$)'
                match = re.search(pattern, markdown, re.DOTALL)
                
                if match:
                    section = match.group(1)
                    category = self._classify_section(section)
                    
                    for p in range(start_page, end_page + 1):
                        classifications.append({"page": p, "category": category, "confidence": 0.85})
        
        # If no classifications, do keyword-based classification on full text
        if not classifications:
            lines = markdown.split('\n')
            lines_per_page = max(1, len(lines) // total_pages)
            
            for page_num in range(1, total_pages + 1):
                start_idx = (page_num - 1) * lines_per_page
                end_idx = min(page_num * lines_per_page, len(lines))
                section = '\n'.join(lines[start_idx:end_idx])
                
                category = self._classify_section(section)
                classifications.append({"page": page_num, "category": category, "confidence": 0.7})
        
        return classifications
    
    def _score_page(self, text: str) -> dict:
        """Score a page for operative, preamble, and procedural characteristics."""
        text_upper = text.upper()
        scores = {"operative": 0, "preamble": 0, "procedural": 0}

        # Strong operative signals
        for kw in ['DIRECTED THAT', 'ORDERED THAT', 'RESPONDENTS ARE DIRECTED',
                   'ACCORDINGLY', 'DISPOSED OF', 'HELD THAT', 'DIRECTED TO']:
            if kw in text_upper:
                scores["operative"] += 4

        # Medium operative
        for kw in ['ORDER', 'COMPLY', 'SUBMIT', 'FILE THEIR', 'WITHIN', 'WEEKS', 'DAYS',
                   'NOTICE', 'ACCEPTS NOTICE']:
            if kw in text_upper:
                scores["operative"] += 1

        # Weak operative (signatures)
        for kw in ['JUDGE', 'SD/-', 'REGISTRAR']:
            if kw in text_upper:
                scores["operative"] += 0.5

        # Numbered paragraphs — light weight
        numbered_para = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
        scores["operative"] += numbered_para * 0.3

        # Preamble — header-only keywords
        for kw in ['PETITIONER', 'RESPONDENT', 'VERSUS', 'V.', 'CASE NO',
                   'WRIT PETITION', 'IN THE HIGH COURT', 'BETWEEN', 'CORAM:']:
            if kw in text_upper:
                scores["preamble"] += 2

        # Procedural
        for kw in ['HEARD', 'APPEAR', 'COUNSEL', 'ARGUED', 'SUBMITTED',
                   'CONSIDERED', 'PERUSED', 'READ', 'NOTED']:
            if kw in text_upper:
                scores["procedural"] += 1

        return scores

    def _find_operative_block(self, classifications: List[dict], total_pages: int) -> List[int]:
        """Find contiguous operative pages by working backwards from the end."""
        last_op_page = None
        for i in range(total_pages - 1, -1, -1):
            c = classifications[i]
            if c["operative_score"] >= 1.0:
                last_op_page = c["page"]
                break

        if last_op_page is None:
            return []

        first_op_page = last_op_page
        for i in range(last_op_page - 2, -1, -1):
            c = classifications[i]
            next_c = classifications[i + 1]

            # Hard stop at clear preamble (only if operative doesn't dominate)
            if c["preamble_score"] >= 4 and c["operative_score"] < c["preamble_score"]:
                break

            # Include if page has operative signal, or is adjacent to strong operative
            has_operative = c["operative_score"] >= 1.5
            adjacent_to_strong = next_c["operative_score"] >= 4.0 and c["operative_score"] >= 1.0 and c["preamble_score"] < 2

            if has_operative or adjacent_to_strong:
                first_op_page = c["page"]
            else:
                break

        return list(range(first_op_page, last_op_page + 1))

    def _find_preamble_block(self, classifications: List[dict]) -> List[int]:
        """Find contiguous preamble pages from the start."""
        preamble_pages = []
        for c in classifications:
            if c["preamble_score"] >= 2:
                preamble_pages.append(c["page"])
            elif preamble_pages:
                # Stop if we hit a page that's clearly not preamble
                if c["operative_score"] > c["preamble_score"]:
                    break
                if c["preamble_score"] == 0 and c["operative_score"] == 0:
                    # Procedural gap — continue briefly
                    if len(preamble_pages) >= 2:
                        break
                else:
                    break
        return preamble_pages

    def _classify_section(self, text: str) -> str:
        """Classify a section of text based on keywords."""
        text_upper = text.upper()
        
        # Operative order indicators
        operative_keywords = ['ORDER', 'DIRECTED THAT', 'ORDERED THAT', 'RESPONDENT SHALL', 
                             'COMPLY', 'DISPOSED OF', 'HELD THAT', 'JUDGMENT']
        
        # Preamble indicators  
        preamble_keywords = ['PETITIONER', 'RESPONDENT', 'VERSUS', 'V.', 'CASE NO', 
                            'WRIT PETITION', 'DATE OF ORDER']
        
        operative_score = sum(1 for kw in operative_keywords if kw in text_upper)
        preamble_score = sum(1 for kw in preamble_keywords if kw in text_upper)
        
        if operative_score > preamble_score and operative_score > 0:
            return "OPERATIVE_ORDER"
        elif preamble_score > operative_score and preamble_score > 0:
            return "PREAMBLE"
        else:
            return "PROCEDURAL_HISTORY"
    
    def _build_page_range(self, pages: List[int]) -> str:
        """Build a compact page range string from a list of page numbers."""
        if not pages:
            return ""
        
        pages = sorted(set(pages))
        ranges = []
        start = pages[0]
        end = pages[0]
        
        for page in pages[1:]:
            if page == end + 1:
                end = page
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = page
        
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ",".join(ranges)
    
    async def _run_pass2(self, db: Session, job: ProcessingJob, judgment: Judgment, sliced_text: str, page_range: str) -> ActionPlan:
        """Run Pass 2: Extract structured action plan using Sarvam-105B."""
        
        text_to_send = sliced_text[:30000]
        try:
            extraction = await sarvam_client.extract_action_plan(text_to_send, page_range)
        except Exception as exc:
            logger.warning("Pass 2 Sarvam extraction failed; using local fallback: %s", exc)
            extraction = self._fallback_extract_action_plan(
                text_to_send, page_range, str(exc)
            )
        
        job.pass2_raw_response = json.dumps(extraction)
        db.flush()
        
        date_of_order = None
        if extraction.get("date_of_order"):
            try:
                date_of_order = datetime.strptime(extraction["date_of_order"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                pass
        
        action_plan = ActionPlan(
            job_id=job.id,
            judgment_id=judgment.id,
            case_id=extraction.get("case_id"),
            date_of_order=date_of_order,
            parties=extraction.get("parties"),
            is_complete=extraction.get("is_complete_info_present", False),
            overall_confidence=extraction.get("overall_confidence"),
            raw_extraction_json=extraction,
            sliced_text=sliced_text[:10000],
            status="PENDING"
        )
        db.add(action_plan)
        db.flush()
        
        directives_data = extraction.get("directives", [])
        for i, d in enumerate(directives_data, 1):
            source_page = d.get("source_page")
            if source_page is not None:
                try:
                    source_page = max(1, min(int(source_page), judgment.total_pages))
                except (TypeError, ValueError):
                    source_page = None

            deadline_explicit = None
            if d.get("deadline_explicit"):
                try:
                    deadline_explicit = datetime.strptime(d["deadline_explicit"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except:
                    pass
            
            deadline_inferred = None
            if d.get("deadline_inferred"):
                try:
                    deadline_inferred = datetime.strptime(d["deadline_inferred"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except:
                    pass
            
            directive = Directive(
                action_plan_id=action_plan.id,
                judgment_id=judgment.id,
                directive_number=i,
                action_type=d.get("action_type", "COMPLY"),
                responsible_dept=d.get("responsible_dept", "Other"),
                deadline_explicit=deadline_explicit,
                deadline_inferred=deadline_inferred,
                source_page=source_page,
                source_paragraph=d.get("source_paragraph"),
                source_text=d.get("source_text"),
                confidence_score=d.get("confidence_score"),
                extracted_json=d,
                status="UNVERIFIED"
            )
            db.add(directive)
        
        db.flush()
        return action_plan

    def _fallback_extract_action_plan(
        self, text: str, page_range: str, error_message: str
    ) -> Dict[str, Any]:
        """Create a reviewable low-confidence plan from real PDF text."""
        order_date = self._extract_order_date(text)
        returnable_date = self._extract_returnable_date(text)
        page_numbers = self._parse_page_range(page_range) if page_range else [1]
        default_page = page_numbers[0] if page_numbers else 1

        directives: List[Dict[str, Any]] = []

        detail_match = re.search(
            r"the respondents are directed to\s+furnish.*?following\s+details.*?(?=The Registrar General|When dictation|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if detail_match:
            block = re.sub(r"\s+", " ", detail_match.group(0)).strip()
            for label, dept, phrase in [
                ("preventive and remedial measures", "Health", "preventive and remedial measures"),
                ("medical facilities", "Health", "medical facilities"),
                ("availability of infrastructure", "Health", "availability of infrastructure"),
                ("public awareness", "Health", "creating public awareness"),
                ("mosquito breeding", "Urban Development", "control the mosquito breeding"),
            ]:
                item = self._extract_sentence_containing(block, phrase) or block[:700]
                directives.append(
                    self._fallback_directive(
                        action_type="COMPLY",
                        responsible_dept=dept,
                        deadline=returnable_date,
                        source_page=default_page,
                        source_paragraph=label,
                        source_text=item,
                        confidence=0.58,
                    )
                )

        registrar = self._extract_sentence_containing(
            text, "Registrar General is directed"
        )
        if registrar:
            directives.append(
                self._fallback_directive(
                    action_type="COMPLY",
                    responsible_dept="Other",
                    deadline=order_date,
                    source_page=page_numbers[-1] if page_numbers else default_page,
                    source_paragraph="registrar procedural direction",
                    source_text=registrar,
                    confidence=0.55,
                )
            )

        reply = self._extract_sentence_containing(
            text, "respondents shall file their replies"
        )
        if reply:
            directives.append(
                self._fallback_directive(
                    action_type="COMPLY",
                    responsible_dept="Law",
                    deadline=returnable_date,
                    source_page=page_numbers[-1] if page_numbers else default_page,
                    source_paragraph="reply filing direction",
                    source_text=reply,
                    confidence=0.57,
                )
            )

        if not directives:
            generic = self._extract_sentence_containing(text, "directed") or text[:700]
            directives.append(
                self._fallback_directive(
                    action_type="COMPLY",
                    responsible_dept="Other",
                    deadline=returnable_date,
                    source_page=default_page,
                    source_paragraph="fallback directive",
                    source_text=generic,
                    confidence=0.45,
                )
            )

        return {
            "case_id": None,
            "date_of_order": order_date,
            "parties": {"petitioner": None, "respondent": None},
            "directives": directives,
            "is_complete_info_present": False,
            "overall_confidence": 0.55,
            "completeness_assessment": (
                "Sarvam extraction failed, so this low-confidence draft was built "
                f"from the real PDF text for nodal officer review. Error: {error_message}"
            ),
        }

    def _fallback_directive(
        self,
        action_type: str,
        responsible_dept: str,
        deadline: Optional[str],
        source_page: int,
        source_paragraph: str,
        source_text: str,
        confidence: float,
    ) -> Dict[str, Any]:
        return {
            "action_type": action_type,
            "responsible_dept": responsible_dept,
            "deadline_explicit": deadline,
            "deadline_inferred": deadline,
            "source_page": source_page,
            "source_paragraph": source_paragraph,
            "source_text": re.sub(r"\s+", " ", source_text).strip(),
            "confidence_score": confidence,
        }

    def _extract_order_date(self, text: str) -> Optional[str]:
        match = re.search(r"Date:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})", text, re.IGNORECASE)
        if not match:
            return None
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    def _extract_returnable_date(self, text: str) -> Optional[str]:
        match = re.search(
            r"returnable on\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None
        day, month_name, year = match.groups()
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        month = months.get(month_name.lower())
        if not month:
            return None
        return f"{year}-{month:02d}-{int(day):02d}"

    def _extract_sentence_containing(self, text: str, phrase: str) -> Optional[str]:
        normalized = re.sub(r"\s+", " ", text)
        pattern = rf"([^.;]*{re.escape(phrase)}[^.;]*(?:[.;]|$))"
        match = re.search(pattern, normalized, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _parse_page_range(self, range_str: str) -> List[int]:
        """Parse '45-52' or '45,46,47-50' into [45, 46, 47, 48, 49, 50]."""
        result = []
        for part in range_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                result.extend(range(int(start), int(end) + 1))
            else:
                result.append(int(part))
        return result

pipeline_service = PipelineService()
