"""One vector layout for both browser preview (SVG) and PDF export."""

from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Path as VectorPath, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WIDTH, HEIGHT = A4
MARGIN = 42
FONT = "ChordAI-NotoSans"


def register_font() -> None:
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, str(Path(__file__).with_name("fonts") / "NotoSans-Regular.ttf")))


def text(page, x, y, value, size=10, anchor="start", color=colors.black):
    page.add(String(x, y, value, fontName=FONT, fontSize=size, textAnchor=anchor, fillColor=color))


def treble_clef(page, x, y):
    # Original vector G-clef, centered around the second line from the bottom.
    p = VectorPath(strokeColor=colors.black, strokeWidth=1.5, fillColor=None)
    p.moveTo(x + 13, y - 11)
    p.curveTo(x + 28, y - 21, x + 17, y + 19, x + 15, y + 34)
    p.curveTo(x + 9, y + 62, x + 27, y + 62, x + 19, y + 42)
    p.curveTo(x + 14, y + 31, x - 4, y + 20, x + 4, y + 8)
    p.curveTo(x + 12, y - 4, x + 33, y + 3, x + 25, y + 18)
    p.curveTo(x + 18, y + 30, x + 5, y + 19, x + 13, y + 11)
    page.add(p)


def label_layout(measure, x, width):
    placed, lane_ends = [], []
    for label in measure["chords"]:
        label_width = pdfmetrics.stringWidth(label["chord"], FONT, 10)
        position = min(x + 10 + label["beat"] / 4 * (width - 22), x + width - label_width - 6)
        lane = next((i for i, end in enumerate(lane_ends) if position >= end + 5), len(lane_ends))
        if lane == len(lane_ends):
            lane_ends.append(0)
        lane_ends[lane] = position + label_width
        placed.append((position, lane, label["chord"]))
    return placed, len(lane_ends)


def score_pages(score: dict) -> list[Drawing]:
    register_font()
    pages = []

    def new_page():
        page = Drawing(WIDTH, HEIGHT)
        page.add(Rect(0, 0, WIDTH, HEIGHT, fillColor=colors.white, strokeColor=None))
        title = " ".join(score["title"].split())
        # Wrap long/unbroken filenames without silently truncating the song title.
        lines, line = [], ""
        for char in title:
            if pdfmetrics.stringWidth(line + char, FONT, 18) > WIDTH - 2 * MARGIN:
                lines.append(line)
                line = ""
            line += char
        lines.append(line)
        title_y = HEIGHT - 50
        for line in lines:
            text(page, WIDTH / 2, title_y, line, 18, "middle")
            title_y -= 24
        text(page, WIDTH / 2, title_y - 2, "CHORD ACCOMPANIMENT", 9, "middle", colors.HexColor("#55616e"))
        tempo = f"Tempo: {score['bpm']:.0f} BPM" if score["bpm"] else "Tempo unavailable"
        text(page, MARGIN, title_y - 31, tempo, 9)
        text(page, WIDTH - MARGIN, title_y - 31, "4/4 (estimated)", 9, "end")
        text(page, MARGIN, title_y - 48, score["notice"], 8, color=colors.HexColor("#55616e"))
        text(page, MARGIN, title_y - 62, score["timing_note"], 8, color=colors.HexColor("#55616e"))
        pages.append(page)
        return page, title_y - 100

    page, top = new_page()
    measures = score["measures"]
    if not measures:
        text(page, WIDTH / 2, top - 55, "No stable chords detected.", 12, "middle")
    index = 0
    while index < len(measures):
        count = min(4, len(measures) - index)
        if any(len(m["chords"]) > 4 for m in measures[index:index + count]):
            count = 1
        elif any(len(m["chords"]) > 2 for m in measures[index:index + count]):
            count = min(2, count)
        row = measures[index:index + count]
        prefix = 54
        width = (WIDTH - 2 * MARGIN - prefix) / count
        layouts = [label_layout(m, MARGIN + prefix + i * width, width) for i, m in enumerate(row)]
        lanes = max(n for _, n in layouts)
        row_height = 100 + (lanes - 1) * 14
        if top - row_height < 76:
            page, top = new_page()
        bottom = top - 56 - (lanes - 1) * 14
        text(page, MARGIN, top + 8, str(row[0]["number"]), 8, color=colors.HexColor("#55616e"))
        for n in range(5):
            page.add(Line(MARGIN, bottom + n * 7, WIDTH - MARGIN, bottom + n * 7, strokeWidth=0.55))
        treble_clef(page, MARGIN + 2, bottom - 2)
        text(page, MARGIN + 40, bottom + 16, "4", 14, "middle")
        text(page, MARGIN + 40, bottom + 2, "4", 14, "middle")
        for i, measure in enumerate(row):
            x = MARGIN + prefix + i * width
            page.add(Line(x, bottom, x, bottom + 28, strokeWidth=0.7))
            for position, lane, name in layouts[i][0]:
                text(page, position, bottom + 40 + lane * 14, name)
                if lane:
                    page.add(Line(position, bottom + 33, position, bottom + 35 + lane * 14,
                                  strokeWidth=0.35, strokeColor=colors.HexColor("#aaaaaa")))
            for beat in range(4):
                if beat >= measure["beats"] - 1e-6:
                    break
                sx = x + 12 + beat / 4 * (width - 22)
                page.add(Polygon([sx, bottom + 7, sx + 3, bottom + 7,
                                  sx + 10, bottom + 21, sx + 7, bottom + 21],
                                 fillColor=colors.black, strokeColor=None))
            page.add(Line(x + width, bottom, x + width, bottom + 28, strokeWidth=0.7))
        if index + count == len(measures):
            page.add(Line(WIDTH - MARGIN - 3, bottom, WIDTH - MARGIN - 3, bottom + 28, strokeWidth=1.8))
        top -= row_height
        index += count
    for number, page in enumerate(pages, 1):
        text(page, MARGIN, 47, "Slashes indicate accompaniment beats. N.C. = no chord / unknown.", 8)
        text(page, MARGIN, 33, "Chord chart only; melody and lyrics are not transcribed.", 8, color=colors.HexColor("#55616e"))
        text(page, WIDTH - MARGIN, 33, f"{number} / {len(pages)}", 8, "end")
    return pages


def preview_pages(score: dict) -> list[str]:
    # Browser uses a system font for text; all notation is vector geometry.
    return [renderSVG.drawToString(page).replace(FONT, "Arial, sans-serif") for page in score_pages(score)]
