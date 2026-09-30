"""Download the official GuitarSet archives and audit audio/chord pairs (stdlib only)."""
import argparse
import hashlib
import json
import math
import shutil
import urllib.request
import wave
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data" / "guitarset"
FILES = {
    "annotation.zip": "b39b78e63d3446f2e54ddb7a54df9b10",
    "audio_mono-mic.zip": "275966d6610ac34999b58426beb119c3",
}
KNOWN_TIMING_ISSUES = {"04_BN3-154-E_comp", "04_Jazz1-200-B_comp"}


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "md5").hexdigest()


def download(root):
    root.mkdir(parents=True, exist_ok=True)
    for name, expected in FILES.items():
        archive = root / name
        if not archive.exists() or checksum(archive) != expected:
            url = f"https://zenodo.org/records/3371780/files/{name}?download=1"
            print(f"Downloading {name} ...", flush=True)
            temporary = archive.with_suffix(".zip.part")
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            if checksum(temporary) != expected:
                raise ValueError(f"Checksum mismatch: {name}; incomplete file retained as .part")
            temporary.replace(archive)
        print(f"Verified {name}", flush=True)
        destination = root / ("annotations" if name == "annotation.zip" else "audio")
        destination.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                target = (destination / item.filename).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise ValueError(f"Unsafe archive member: {item.filename}")
            bundle.extractall(destination)


def audit(root):
    annotations = sorted((root / "annotations").rglob("*.jams"))
    if len(annotations) != 360:
        raise ValueError(f"Expected 360 annotations, found {len(annotations)}; run with --download")
    audio = {p.stem.removesuffix("_mic"): p for p in (root / "audio").rglob("*.wav")}
    if len(audio) != 360:
        raise ValueError(f"Expected 360 audio recordings, found {len(audio)}")
    rows, problems = [], []
    labels = Counter()
    metadata_examples = []
    for path in annotations:
        track = path.stem
        wav = audio.get(track)
        if wav is None:
            problems.append(f"Missing audio: {track}")
            continue
        with wave.open(str(wav), "rb") as stream:
            duration = stream.getnframes() / stream.getframerate()
            sample_rate = stream.getframerate()
            channels = stream.getnchannels()
        document = json.loads(path.read_text(encoding="utf-8"))
        chords = [a for a in document["annotations"] if a["namespace"] == "chord"]
        if len(chords) != 2:
            problems.append(f"Expected two chord annotation variants: {track}")
        variants = []
        for annotation in chords:
            metadata = annotation.get("annotation_metadata", {})
            if metadata not in metadata_examples:
                metadata_examples.append(metadata)
            previous_end = 0.0
            for event in annotation["data"]:
                start, length = event["time"], event["duration"]
                if (not math.isfinite(start) or not math.isfinite(length)
                        or start < 0 or length <= 0 or start < previous_end - 0.001
                        or start + length > duration + 0.1):
                    problems.append(f"Invalid chord interval: {track}: {event}")
                previous_end = start + length
            variants.append({"metadata": metadata, "segments": annotation["data"]})
            labels.update(e["value"] for e in annotation["data"])
        rows.append({
            "track_id": track,
            "audio": wav.relative_to(root).as_posix(),
            "annotation": path.relative_to(root).as_posix(),
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "exclude_pending_review": track in KNOWN_TIMING_ISSUES,
            "chord_variants": variants,
        })
    report = {
        "source": "https://zenodo.org/records/3371780",
        "version": "1.1.0",
        "recordings": len(rows),
        "audio_hours": sum(r["duration_seconds"] for r in rows) / 3600,
        "known_timing_issues": sorted(KNOWN_TIMING_ISSUES),
        "annotation_metadata_examples": metadata_examples,
        "label_counts_both_variants": dict(labels.most_common()),
        "problems": problems,
        "scope": "Structural audit only; no listening validation, label reduction, split or CNN training yet.",
    }
    (root / "manifest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (root / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {
        "label_counts_both_variants", "annotation_metadata_examples"}}, indent=2))
    if problems:
        raise ValueError("Dataset audit found problems; see audit.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download and verify ~696 MB, then extract")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.download:
        download(args.root)
    audit(args.root)
