"""
Domain Layer — Validation Service
Pure business rules, zero external I/O.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from app.domain.entities.entities import QRSettingsEntity


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: Optional[str] = None

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True)

    @classmethod
    def fail(cls, message: str) -> "ValidationResult":
        return cls(valid=False, error=message)


_URL_PATTERN = re.compile(
    r"^(https?://)"                   # scheme required
    r"([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,})"  # domain
    r"(:\d+)?"                         # optional port
    r"(/[^\s]*)?"                      # optional path
    r"(\?[^\s]*)?"                     # optional query
    r"(#[^\s]*)?$",                    # optional fragment
    re.IGNORECASE,
)


class URLValidationService:
    """Domain rule: what counts as a valid URL for QR encoding."""

    def validate(self, url: str) -> ValidationResult:
        if not url or not url.strip():
            return ValidationResult.fail("URL cannot be empty.")
        stripped = url.strip()
        if len(stripped) > 2048:
            return ValidationResult.fail("URL exceeds maximum length of 2048 characters.")
        if not _URL_PATTERN.match(stripped):
            return ValidationResult.fail(
                "Enter a valid URL starting with http:// or https://"
            )
        return ValidationResult.ok()


class QRSettingsValidationService:
    """Domain rule: sanity-check QR settings before generation."""

    def validate(self, settings: QRSettingsEntity) -> ValidationResult:
        if settings.box_size < 1 or settings.box_size > 50:
            return ValidationResult.fail("Box size must be between 1 and 50.")
        if settings.border < 0 or settings.border > 20:
            return ValidationResult.fail("Border must be between 0 and 20.")
        if settings.image_size < 100 or settings.image_size > 4000:
            return ValidationResult.fail("Image size must be between 100 and 4000 pixels.")
        if not _is_hex_color(settings.fg_color):
            return ValidationResult.fail("Foreground color is not a valid hex color.")
        if not _is_hex_color(settings.bg_color):
            return ValidationResult.fail("Background color is not a valid hex color.")
        if settings.fg_color.upper() == settings.bg_color.upper():
            return ValidationResult.fail(
                "Foreground and background colors must be different."
            )
        return ValidationResult.ok()


def _is_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", value))
