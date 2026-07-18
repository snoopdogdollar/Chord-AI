from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ExportFailedError, ExportNotFoundError, SongNotFoundError
from app.exports.exporter import export_pdf, export_txt
from app.repositories import AnalysisRepository, SongRepository


class ExportService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.songs = SongRepository(db)
        self.analysis = AnalysisRepository(db)

    def create_export(self, song_id: str, export_format: str) -> dict:
        if export_format not in self.settings.allowed_export_formats:
            raise ExportFailedError("Unsupported export format")
        song = self.songs.get(song_id)
        if not song:
            raise SongNotFoundError("Song was not found")
        sheet = self.analysis.latest_sheet(song_id)
        if not sheet:
            raise ExportFailedError("No generated sheet is available")

        target = self.settings.exports_dir / f"{song_id}.{export_format}"
        if export_format == "txt":
            export_txt(sheet.content, target)
        else:
            export_pdf(song.title, sheet.content, target)

        export = self.analysis.create_export(song_id, export_format, str(target))
        return {"export_id": export.id, "download_url": f"/api/v1/exports/{export.id}"}

    def get_export_path(self, export_id: str) -> tuple[Path, str]:
        export = self.analysis.get_export(export_id)
        if not export:
            raise ExportNotFoundError("Export was not found")
        path = Path(export.file_path)
        if not path.exists():
            raise ExportNotFoundError("Export file is missing")
        return path, export.export_format
