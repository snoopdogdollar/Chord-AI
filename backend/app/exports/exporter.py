from pathlib import Path

from app.core.errors import ExportFailedError


def export_txt(content: str, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path


def export_pdf(title: str, content: str, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise ExportFailedError("reportlab is required for PDF export") from exc

    pdf = canvas.Canvas(str(target_path), pagesize=letter)
    width, height = letter
    y = height - 54
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(54, y, title)
    y -= 30
    pdf.setFont("Courier", 10)
    for line in content.splitlines():
        if y < 54:
            pdf.showPage()
            y = height - 54
            pdf.setFont("Courier", 10)
        pdf.drawString(54, y, line[:100])
        y -= 14
    pdf.save()
    return target_path
