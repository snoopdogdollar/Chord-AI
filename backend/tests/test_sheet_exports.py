from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_settings
from app.api.router import api_router
from app.chords.models import ChordEvent
from app.core.config import Settings
from app.db.session import Base
from app.repositories import AnalysisRepository, JobRepository, SongRepository
from app.services.pipeline_runner import PipelineRunner
from app.sheets.score import build_score, decode_score, encode_score


@pytest.fixture
def score_api(tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        settings = Settings(storage_root=tmp_path)
        app = FastAPI()
        app.include_router(api_router, prefix="/api/v1")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_settings] = lambda: settings
        song = SongRepository(db).create(title="Mưa và nắng", source_type="upload", source_url=None,
                                         original_path="test.wav")
        SongRepository(db).update_analysis(song, processed_path="test.wav", duration=4, bpm=120)
        analysis = AnalysisRepository(db)
        analysis.replace_chords(song.id, [ChordEvent(0, 4, "Am7", .9).to_dict()])
        with TestClient(app) as client:
            yield client, song, analysis, db, settings
    engine.dispose()


@pytest.mark.parametrize("legacy", [True, False])
def test_preview_and_pdf_download_for_old_and_new_sheets(score_api, legacy):
    client, song, analysis, _, _ = score_api
    score = build_score(song.title, [ChordEvent(0, 4, "Am7", .9)], bpm=120)
    analysis.create_sheet(song.id, "Old text sheet" if legacy else encode_score(score))
    preview = client.get(f"/api/v1/songs/{song.id}/sheet")
    assert preview.status_code == 200
    payload = preview.json()["data"]
    assert "<svg" in payload["pages"][0]
    assert "Am7" in payload["pages"][0]
    assert payload["title"] == song.title
    response = client.post(f"/api/v1/songs/{song.id}/export", json={"format": "pdf"})
    assert response.status_code == 200
    download = client.get(response.json()["data"]["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF-")
    # The legacy TXT API remains valid, and never leaks the stored JSON document.
    txt = client.post(f"/api/v1/songs/{song.id}/export", json={"format": "txt"}).json()["data"]
    body = client.get(txt["download_url"]).text
    assert "[Song]" in body and "Am7" in body
    assert '"version": 2' not in body


def test_pipeline_saves_detected_beat_grid(score_api):
    from app.audio.models import BeatMap, FeatureSet
    _, song, analysis, db, settings = score_api
    job = JobRepository(db).create(song.id)
    features = FeatureSet([], [], 44100, 512, 4)
    beats = BeatMap(120, [0, .5, 1.2, 2.3, 3, 3.5])
    module = "app.services.pipeline_runner."
    with patch(module + "convert_to_wav", return_value=Path("test.wav")), \
         patch(module + "normalize_audio", return_value=Path("test.wav")), \
         patch(module + "extract_chroma_features", return_value=features), \
         patch(module + "detect_beats", return_value=beats), \
         patch(module + "ChordDetector.detect", return_value=[ChordEvent(0, 4, "C", .9)]):
        PipelineRunner(db, settings).run_job(job.id)
    assert job.status == "completed", job.error_message
    score = decode_score(analysis.latest_sheet(song.id).content)
    assert score["grid_source"] == "detected_beats"
    assert score["measures"][0]["end"] == 3
