from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.core.config import Settings
from app.core.responses import success_response
from app.db.session import SessionLocal
from app.schemas import YouTubeRequest
from app.services.pipeline_runner import PipelineRunner
from app.services.songs import SongService

router = APIRouter(prefix="/songs", tags=["songs"])


def enqueue_processing(background_tasks: BackgroundTasks, job_id: str, settings: Settings) -> None:
    def task() -> None:
        db = SessionLocal()
        try:
            PipelineRunner(db, settings).run_job(job_id)
        finally:
            db.close()

    background_tasks.add_task(task)


@router.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    song_id, job_id = await SongService(db, settings).create_from_upload(file)
    enqueue_processing(background_tasks, job_id, settings)
    return success_response({"song_id": song_id, "job_id": job_id, "status": "queued"})


@router.post("/youtube")
def process_youtube(
    request: YouTubeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    song_id, job_id = SongService(db, settings).create_from_youtube(request.url)
    enqueue_processing(background_tasks, job_id, settings)
    return success_response({"song_id": song_id, "job_id": job_id, "status": "queued"})


@router.get("/{song_id}")
def get_song(song_id: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return success_response(SongService(db, settings).get_song_payload(song_id))


@router.get("/{song_id}/chords")
def get_chords(song_id: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return success_response(SongService(db, settings).get_chords_payload(song_id))


@router.get("/{song_id}/sheet")
def get_sheet(song_id: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return success_response(SongService(db, settings).get_sheet_payload(song_id))
