"""
Domain Layer — Entities
Pure data classes with no external dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ErrorCorrectionLevel(str, Enum):
    L = "L"  # ~7% recovery
    M = "M"  # ~15% recovery
    Q = "Q"  # ~25% recovery
    H = "H"  # ~30% recovery


@dataclass
class QRSettingsEntity:
    """All user-configurable parameters for QR generation."""
    url: str = ""
    fg_color: str = "#000000"
    bg_color: str = "#FFFFFF"
    box_size: int = 10          # pixels per module
    border: int = 4             # quiet-zone modules
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.M
    add_quiet_zone: bool = True
    image_size: int = 300       # output image dimension (pixels)

    def effective_border(self) -> int:
        return self.border if self.add_quiet_zone else 0


@dataclass
class QRCodeEntity:
    """Result of a QR generation operation."""
    settings: QRSettingsEntity
    image_data: bytes           # raw PNG bytes
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[str] = None    # set after persistence

    @property
    def url(self) -> str:
        return self.settings.url


@dataclass
class HistoryItemEntity:
    """Lightweight record kept in history."""
    id: str
    url: str
    fg_color: str
    bg_color: str
    error_correction: str
    image_size: int
    created_at: datetime
    thumbnail_data: bytes       # small PNG for sidebar preview
