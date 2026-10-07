# ChordAI

ChordAI is a local-first MVP that turns uploaded audio files or YouTube URLs into readable chord sheets.

The MVP intentionally stays small:

- FastAPI backend
- SQLite persistence
- in-process background jobs
- DSP-first chord detection with CQT chroma and template matching
- TXT and PDF exports only
- simple desktop web UI

The result is a staff-based chord accompaniment sheet with estimated 4/4 bars, beat slashes,
and chord symbols. Preview the pages in the app and download a vector PDF. Meter/downbeats are
estimated; melody and lyrics are not transcribed. See [Staff sheet v1](docs/staff-sheet-v1.md)
for timing assumptions and compatibility with earlier analyses.

No deep learning, realtime processing, manual chord editing, transposition, MusicXML, MIDI, or automatic song-section recognition are included in the MVP.

## Project Structure

```text
backend/   FastAPI API, jobs, storage, audio pipeline, chords, sheets, exports
frontend/  Next.js desktop MVP workflow
docs/      MVP implementation notes and contracts
tests/     Reserved for cross-system tests
data/      Runtime storage created by the backend
```

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --port 8000
```

The backend API base URL is `http://localhost:8000/api/v1`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend dev server defaults to `http://localhost:3000`.

## Docker Deployment

The easiest local deployment path is Docker. You only need Docker Desktop installed; Python, Node, ffmpeg, and app packages are installed inside the containers.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/health`

Runtime files are stored in the Docker volume `chordai-data`.

For non-Docker backend development, copy `backend/.env.example` to `backend/.env`.

## Tests

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover backend/tests
```

Full API and DSP verification requires installing the backend dependencies and having `ffmpeg` available on `PATH`.
