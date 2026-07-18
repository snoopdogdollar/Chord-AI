from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.errors import JobNotFoundError
from app.core.responses import success_response
from app.repositories import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = JobRepository(db).get(job_id)
    if not job:
        raise JobNotFoundError("Job was not found")
    return success_response(
        {
            "job_id": job.id,
            "song_id": job.song_id,
            "status": job.status,
            "progress": job.progress,
            "stage": job.stage,
            "error_code": job.error_code,
            "error_message": job.error_message,
        }
    )
