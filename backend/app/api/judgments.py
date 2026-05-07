import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.all import Judgment, ProcessingJob
from app.schemas.__init__ import (
    JudgmentResponse, JudgmentListResponse, PipelineTriggerResponse,
    JobStatusResponse
)
from app.services.pipeline_service import pipeline_service
from app.services.alert_engine import alert_engine

router = APIRouter(prefix="/judgments", tags=["judgments"])

@router.post("/upload", response_model=PipelineTriggerResponse)
async def upload_judgment(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ccms_case_id: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload a judgment PDF and trigger the pipeline."""
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")
    
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 50MB.")
    
    from app.services.pdf_service import pdf_service
    file_path, page_count = pdf_service.save_upload(file_bytes, f"{uuid4()}_{file.filename}")
    
    if not ccms_case_id:
        ccms_case_id = file.filename.replace(".pdf", "")
    
    judgment = Judgment(
        ccms_case_id=ccms_case_id,
        file_name=file.filename,
        file_path=file_path,
        file_size_bytes=len(file_bytes),
        total_pages=page_count,
        status="PENDING"
    )
    db.add(judgment)
    db.commit()
    db.refresh(judgment)
    
    # Trigger pipeline in background
    background_tasks.add_task(
        _run_pipeline_background, str(judgment.id)
    )
    
    return PipelineTriggerResponse(
        job_id=uuid4(),  # Placeholder, actual job created in background
        judgment_id=judgment.id,
        status="PENDING",
        message="Upload successful. Pipeline started in background."
    )

async def _run_pipeline_background(judgment_id: str):
    """Background task to run pipeline."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        job = await pipeline_service.run_pipeline(db, judgment_id)
        # Generate alerts after pipeline completes
        alert_engine.generate_alerts(db, judgment_id)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Pipeline failed for judgment {judgment_id}: {e}")
    finally:
        db.close()

@router.get("/", response_model=list[JudgmentListResponse])
def list_judgments(db: Session = Depends(get_db)):
    """List all judgments with their status."""
    judgments = db.query(Judgment).order_by(Judgment.created_at.desc()).all()
    return judgments

@router.get("/{judgment_id}", response_model=JudgmentResponse)
def get_judgment(judgment_id: str, db: Session = Depends(get_db)):
    judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
    if not judgment:
        raise HTTPException(404, "Judgment not found")
    return judgment

@router.get("/{judgment_id}/pdf")
def get_judgment_pdf(judgment_id: str, db: Session = Depends(get_db)):
    """Serve the original uploaded PDF for verification-side preview."""
    judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
    if not judgment:
        raise HTTPException(404, "Judgment not found")
    if not judgment.file_path or not os.path.exists(judgment.file_path):
        raise HTTPException(404, "Judgment PDF file not found")
    return FileResponse(
        judgment.file_path,
        media_type="application/pdf",
        filename=judgment.file_name or os.path.basename(judgment.file_path),
    )
