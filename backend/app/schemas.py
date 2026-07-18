from pydantic import BaseModel, Field


class YouTubeRequest(BaseModel):
    url: str


class ExportRequest(BaseModel):
    format: str = Field(pattern="^(txt|pdf)$")


class JobResponse(BaseModel):
    job_id: str
    song_id: str
    status: str
    progress: int
    stage: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class SongResponse(BaseModel):
    song_id: str
    title: str
    duration: float | None
    bpm: float | None
    key: None = None
    status: str


class ChordResponse(BaseModel):
    start: float
    end: float
    chord: str
    confidence: float
