"""Generate ground truth annotations for benchmark audio files."""
import json
from pathlib import Path

ANNOTATIONS_DIR = Path(__file__).parent / "annotations"


def generate_rock_backing():
    """Rock Backing Track C Major 100 BPM: known C-G-Am-F repeating pattern."""
    bpm = 99.4
    bar_dur = (60.0 / bpm) * 4  # 4 beats per bar
    start = 10.0  # after drum intro
    duration = 239.04
    chords = ["C", "G", "Am", "F"]

    annotations = []
    t = start
    cycle = 0
    while t + bar_dur <= duration:
        chord = chords[cycle % 4]
        end = round(t + bar_dur, 2)
        annotations.append({"start": round(t, 2), "end": end, "chord": chord})
        t = end
        cycle += 1

    data = {
        "title": "Rock Backing Track C Major 100 BPM (C-G-Am-F)",
        "source": "TGuitar YouTube - chord progression known from title",
        "notes": f"100 BPM, 4/4 time. {len(annotations)} bars generated. Intro (0-10s) is drums only.",
        "annotations": annotations,
    }

    path = ANNOTATIONS_DIR / "rock_backing_c_major.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rock Backing: {len(annotations)} annotations, {annotations[0]['start']}s - {annotations[-1]['end']}s")
    for a in annotations[:8]:
        print(f"  {a['start']:>7.2f}s - {a['end']:>7.2f}s  {a['chord']}")


def generate_chay_ngay_di():
    """Chạy Ngay Đi (ONIONN Remix) - Sơn Tùng M-TP.

    Chord progression from Hợp Âm Chuẩn: Bb(A#) - C - Dm - Am repeating.
    126 BPM, 4/4 time. Each chord = 1 bar.
    This is a remix with steady repeating chord pattern.
    Note: Bb and A# are enharmonic - our detector uses sharps.
    """
    bpm = 126.0
    bar_dur = (60.0 / bpm) * 4  # ~1.905s per bar
    start = 9.5  # after intro
    duration = 316.39
    # From Hợp Âm Chuẩn: Bbmaj7 - C - Dm - Am
    # Simplified for major/minor: A# - C - Dm - Am
    chords = ["A#", "C", "Dm", "Am"]

    annotations = []
    t = start
    cycle = 0
    while t + bar_dur <= duration - 5.0:  # leave ~5s for outro
        chord = chords[cycle % 4]
        end = round(t + bar_dur, 2)
        annotations.append({"start": round(t, 2), "end": end, "chord": chord})
        t = end
        cycle += 1

    data = {
        "title": "Chạy Ngay Đi (ONIONN Remix) - Sơn Tùng M-TP",
        "source": "hopamchuan.com - Bb(A#)-C-Dm-Am repeating pattern",
        "notes": (
            f"126 BPM, 4/4 time. {len(annotations)} bars. "
            "APPROXIMATE TIMING - needs user verification against audio. "
            "Remix version has a steady repeating chord loop."
        ),
        "annotations": annotations,
    }

    path = ANNOTATIONS_DIR / "chay_ngay_di.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Chạy Ngay Đi: {len(annotations)} annotations, {annotations[0]['start']}s - {annotations[-1]['end']}s")
    for a in annotations[:8]:
        print(f"  {a['start']:>7.2f}s - {a['end']:>7.2f}s  {a['chord']}")


def generate_neu_nhu_ta_chang_con():
    """Nếu Như Ta Chẳng Còn - MCK.

    From Hợp Âm Chuẩn: Tone Dm, complex structure.
    BPM detected as 184.6 (likely double-time, real BPM ~92.3).
    Verse: Gm - A - Dm - Bb(A#)
    Chorus: Gm - C - F - Bb(A#), Gm - A - Dm

    Since this has complex verse/chorus structure with varying chord lengths,
    we use a simplified repeating pattern approach for the verse sections
    and note that this needs extensive manual verification.
    """
    # Real BPM is ~92 (detected 184.6 is double-time)
    bpm = 92.3
    bar_dur = (60.0 / bpm) * 4  # ~2.6s per bar
    duration = 314.81

    # The song has a more complex structure. Using the main verse pattern.
    # Verse pattern (from Hợp Âm Chuẩn): Gm - A - Dm - A# (Bb)
    # Chorus pattern: Gm - C - F - A# (Bb), then Gm - A - Dm

    # Simplified approach: use the repeating verse pattern
    # and mark the entire file as needing verification
    verse_chords = ["Gm", "A", "Dm", "A#"]
    chorus_chords = ["Gm", "C", "F", "A#", "Gm", "A", "Dm", "Dm"]

    # Approximate song structure (very rough):
    # 0-5s: intro
    # 5s-80s: verse 1 (Gm-A-Dm-A# repeating)
    # 80s-120s: chorus 1 (Gm-C-F-A#, Gm-A-Dm)
    # 120s-190s: verse 2
    # 190s-230s: chorus 2
    # 230s-280s: bridge/verse 3
    # 280s-315s: outro/chorus

    annotations = []
    sections = [
        (5.0, 80.0, verse_chords),
        (80.0, 120.0, chorus_chords),
        (120.0, 190.0, verse_chords),
        (190.0, 230.0, chorus_chords),
        (230.0, 280.0, verse_chords),
        (280.0, 310.0, chorus_chords),
    ]

    for section_start, section_end, chords in sections:
        t = section_start
        cycle = 0
        while t + bar_dur <= section_end:
            chord = chords[cycle % len(chords)]
            end = round(t + bar_dur, 2)
            annotations.append({"start": round(t, 2), "end": end, "chord": chord})
            t = end
            cycle += 1

    data = {
        "title": "Nếu Như Ta Chẳng Còn - MCK",
        "source": "hopamchuan.com - Tone Dm",
        "notes": (
            f"~92 BPM, 4/4 time. {len(annotations)} bars. "
            "WARNING: VERY APPROXIMATE. Song has complex verse/chorus structure. "
            "Section boundaries and chord timings are estimated and MUST be verified "
            "by listening to the audio. This annotation should be treated as a rough draft."
        ),
        "annotations": annotations,
    }

    path = ANNOTATIONS_DIR / "neu_nhu_ta_chang_con.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Nếu Như Ta Chẳng Còn: {len(annotations)} annotations, {annotations[0]['start']}s - {annotations[-1]['end']}s")
    for a in annotations[:8]:
        print(f"  {a['start']:>7.2f}s - {a['end']:>7.2f}s  {a['chord']}")


if __name__ == "__main__":
    generate_rock_backing()
    print()
    generate_chay_ngay_di()
    print()
    generate_neu_nhu_ta_chang_con()
