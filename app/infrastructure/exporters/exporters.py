"""
Infrastructure Layer — Export Adapters
Each exporter is independent and swappable.
"""
from __future__ import annotations
import io
from pathlib import Path
from typing import Protocol

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


class IExporter(Protocol):
    extension: str

    def export(self, png_bytes: bytes, destination: Path) -> None:
        ...


class PNGExporter:
    extension = ".png"

    def export(self, png_bytes: bytes, destination: Path) -> None:
        destination.write_bytes(png_bytes)


class JPGExporter:
    extension = ".jpg"

    def export(self, png_bytes: bytes, destination: Path) -> None:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        img.save(destination, format="JPEG", quality=95)


class PDFExporter:
    extension = ".pdf"

    def export(self, png_bytes: bytes, destination: Path) -> None:
        img = Image.open(io.BytesIO(png_bytes))
        img_w, img_h = img.size

        page_w, page_h = A4
        margin = 72  # 1 inch in points

        available_w = page_w - 2 * margin
        available_h = page_h - 2 * margin

        scale = min(available_w / img_w, available_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2

        c = canvas.Canvas(str(destination), pagesize=A4)
        c.drawImage(
            ImageReader(io.BytesIO(png_bytes)),
            x, y, width=draw_w, height=draw_h,
            preserveAspectRatio=True,
        )
        c.save()


class SVGExporter:
    """Generates a minimal SVG wrapping the PNG as an embedded image."""
    extension = ".svg"

    def export(self, png_bytes: bytes, destination: Path) -> None:
        import base64
        b64 = base64.b64encode(png_bytes).decode()
        img = Image.open(io.BytesIO(png_bytes))
        w, h = img.size
        svg = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'  <image width="{w}" height="{h}" '
            f'xlink:href="data:image/png;base64,{b64}"/>\n'
            f'</svg>\n'
        )
        destination.write_text(svg, encoding="utf-8")


EXPORTER_MAP: dict[str, IExporter] = {
    "PNG": PNGExporter(),
    "JPG": JPGExporter(),
    "PDF": PDFExporter(),
    "SVG": SVGExporter(),
}
