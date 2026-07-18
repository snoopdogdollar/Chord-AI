# MVP Implementation Notes

This repository implements the documented MVP only.

## Decisions Locked For MVP

- Backend: FastAPI.
- Frontend: Next.js and TypeScript.
- Database: SQLite through SQLAlchemy.
- Migrations: Alembic, with the MVP schema in `backend/alembic/versions`.
- Background jobs: FastAPI in-process background tasks with persisted job state.
- Audio: ffmpeg for conversion/normalization, librosa CQT chroma, librosa beat tracking.
- Chords: fixed major, minor, dominant 7, and minor 7 templates with cosine similarity.
- Smoothing: majority window, duplicate merge, short-event merge, light beat snapping.
- Exports: TXT and PDF only.

## Explicit Deferrals

- Deep learning.
- Automatic section recognition.
- Key detection.
- Manual chord editing.
- Transposition.
- MusicXML and MIDI.
- WebSockets.
- Authentication.
- Cloud storage.

## Runtime Requirements

- Python 3.12 or compatible.
- Node 20 or compatible.
- ffmpeg on `PATH`.
- `yt-dlp` for YouTube input.

## API Summary

- `POST /api/v1/songs/upload`
- `POST /api/v1/songs/youtube`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/songs/{song_id}`
- `GET /api/v1/songs/{song_id}/chords`
- `GET /api/v1/songs/{song_id}/sheet`
- `POST /api/v1/songs/{song_id}/export`
- `GET /api/v1/exports/{export_id}`

All JSON responses use the documented `success/data` or `success/error` envelope.
