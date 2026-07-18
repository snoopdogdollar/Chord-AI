from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.core.config import Settings
from app.core.responses import success_response
from app.schemas import ExportRequest
from app.services.exports import ExportService

router = APIRouter(tags=["exports"])


@router.post("/songs/{song_id}/export")
def create_export(
    song_id: str,
    request: ExportRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return success_response(ExportService(db, settings).create_export(song_id, request.format))


@router.get("/exports/{export_id}")
def download_export(export_id: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    path, export_format = ExportService(db, settings).get_export_path(export_id)
    media_type = "application/pdf" if export_format == "pdf" else "text/plain"
    return FileResponse(path, media_type=media_type, filename=path.name)
