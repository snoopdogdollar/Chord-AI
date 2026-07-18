from app.chords.models import ChordEvent


def generate_sheet_text(title: str, chords: list[ChordEvent], *, chords_per_line: int = 4) -> str:
    lines = [title.strip() or "Untitled Song", "", "[Song]"]
    if not chords:
        lines.append("No stable chords detected.")
        return "\n".join(lines).strip() + "\n"

    row: list[str] = []
    for chord in chords:
        row.append(f"{chord.chord:<8}")
        if len(row) == chords_per_line:
            lines.append("".join(row).rstrip())
            row = []
    if row:
        lines.append("".join(row).rstrip())

    lines.append("")
    lines.append("Timeline")
    for chord in chords:
        lines.append(f"{chord.start:>7.2f}s - {chord.end:>7.2f}s  {chord.chord:<6}  {chord.confidence:.2f}")
    return "\n".join(lines).strip() + "\n"


def generate_sheet_payload(title: str, content: str) -> dict:
    return {
        "title": title,
        "sections": [
            {
                "name": "Song",
                "content": content.splitlines(),
            }
        ],
    }
