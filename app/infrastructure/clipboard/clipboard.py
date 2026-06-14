"""
Infrastructure Layer — Clipboard Adapter
"""
from __future__ import annotations
import io

from PIL import Image


class ClipboardAdapter:
    """Copies a PNG byte buffer into the system clipboard as an image."""

    def copy_png(self, png_bytes: bytes) -> None:
        from PySide6.QtGui import QImage  # lazy — only needed at runtime
        from PySide6.QtWidgets import QApplication
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        q_image = QImage(
            data,
            img.width,
            img.height,
            QImage.Format.Format_RGBA8888,
        )
        clipboard = QApplication.clipboard()
        clipboard.setImage(q_image)
