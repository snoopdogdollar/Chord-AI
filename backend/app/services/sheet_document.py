from app.chords.models import ChordEvent
from app.sheets.score import build_score, decode_score


def resolve_score(song, sheet, analysis) -> dict:
    """Read new scores or adapt existing analyses without a migration or re-analysis."""
    saved = decode_score(sheet.content) if sheet else None
    if saved is not None:
        return saved
    chords = [ChordEvent(c.timestamp_start, c.timestamp_end, c.chord_name, c.confidence)
              for c in analysis.list_chords(song.id)] if sheet else []
    return build_score(song.title, chords, duration=song.duration, bpm=song.bpm)
