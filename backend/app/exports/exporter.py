from pathlib import Path

from app.core.errors import ExportFailedError


def export_txt(content: str, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path


def export_pdf(score: dict, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.graphics import renderPDF
        from reportlab.pdfgen import canvas
        from app.sheets.notation import score_pages
    except ImportError as exc:
        raise ExportFailedError("reportlab is required for PDF export") from exc

    pages = score_pages(score)
    pdf = canvas.Canvas(str(target_path), pagesize=(pages[0].width, pages[0].height))
    pdf.setTitle(score["title"])
    for page in pages:
        renderPDF.draw(page, pdf, 0, 0)
        pdf.showPage()
    pdf.save()
    return target_path
