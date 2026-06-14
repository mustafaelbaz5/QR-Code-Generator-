"""
Infrastructure Layer — QR Code Generator
Wraps the `qrcode` library. Returns raw PNG bytes.
"""
from __future__ import annotations
import io
from typing import Protocol

import qrcode
from PIL import Image

from app.domain.entities.entities import QRCodeEntity, QRSettingsEntity, ErrorCorrectionLevel

_EC_MAP = {
    ErrorCorrectionLevel.L: qrcode.constants.ERROR_CORRECT_L,
    ErrorCorrectionLevel.M: qrcode.constants.ERROR_CORRECT_M,
    ErrorCorrectionLevel.Q: qrcode.constants.ERROR_CORRECT_Q,
    ErrorCorrectionLevel.H: qrcode.constants.ERROR_CORRECT_H,
}


class IQRGenerator(Protocol):
    def generate(self, settings: QRSettingsEntity) -> bytes:
        """Return raw PNG image bytes for the given settings."""
        ...


class QRCodeGenerator:
    """Concrete implementation using the `qrcode` library."""

    def generate(self, settings: QRSettingsEntity) -> bytes:
        ec_level = _EC_MAP.get(settings.error_correction, qrcode.constants.ERROR_CORRECT_M)

        qr = qrcode.QRCode(
            version=None,           # auto-select smallest
            error_correction=ec_level,
            box_size=settings.box_size,
            border=settings.effective_border(),
        )
        qr.add_data(settings.url.strip())
        qr.make(fit=True)

        img: Image.Image = qr.make_image(
            fill_color=settings.fg_color,
            back_color=settings.bg_color,
        ).convert("RGB")

        # Resize to target dimension preserving crispness
        target = settings.image_size
        img = img.resize((target, target), Image.NEAREST)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def generate_thumbnail(self, png_bytes: bytes, size: int = 80) -> bytes:
        """Downscale PNG bytes to a thumbnail for the history sidebar."""
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        img.thumbnail((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
