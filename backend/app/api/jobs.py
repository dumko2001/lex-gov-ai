from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.all import ProcessingJob
from app.schemas.__init__ import JobStatusResponse, ProcessingJobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=ProcessingJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/judgment/{judgment_id}", response_model=ProcessingJobResponse)
def get_latest_job_for_judgment(judgment_id: str, db: Session = Depends(get_db)):
    """Get latest processing job for a judgment (useful after async upload trigger)."""
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.judgment_id == judgment_id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(404, "No job found for judgment")
    return job


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    progress_map = {
        "PENDING": "Waiting to start",
        "PASS1_RUNNING": "Analyzing document structure (Pass 1)",
        "PASS1_COMPLETE": "Structure identified, slicing PDF",
        "SLICING_COMPLETE": "Extracting action plan (Pass 2)",
        "PASS2_COMPLETE": "Checking completeness",
        "SELF_CORRECTION_LOOP": f"Refining extraction (iteration {job.iteration_count}/{job.max_iterations})",
        "NEEDS_REVIEW": "Ready for nodal officer verification",
        "VERIFIED": "Verified and published to dashboard",
        "FAILED": "Processing failed",
    }

    return JobStatusResponse(
        job_id=job.id,
        judgment_id=job.judgment_id,
        status=job.status,
        iteration_count=job.iteration_count,
        progress=progress_map.get(job.status, job.status),
    )
