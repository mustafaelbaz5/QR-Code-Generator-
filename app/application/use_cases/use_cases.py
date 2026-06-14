"""
Application Layer — Use Cases
All business flows live here. UI knows nothing about QR logic.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.domain.entities.entities import QRCodeEntity, QRSettingsEntity, HistoryItemEntity
from app.domain.services.validation import (
    URLValidationService,
    QRSettingsValidationService,
    ValidationResult,
)
from app.infrastructure.qr.generator import QRCodeGenerator
from app.infrastructure.exporters.exporters import EXPORTER_MAP
from app.infrastructure.storage.history_repository import HistoryRepository
from app.infrastructure.clipboard.clipboard import ClipboardAdapter


# ─────────────────────────────────────────────────────────────────────────────
# Validate URL
# ─────────────────────────────────────────────────────────────────────────────

class ValidateURLUseCase:
    def __init__(self, service: URLValidationService) -> None:
        self._service = service

    def execute(self, url: str) -> ValidationResult:
        return self._service.validate(url)


# ─────────────────────────────────────────────────────────────────────────────
# Generate QR Code
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GenerateQRResult:
    success: bool
    qr: Optional[QRCodeEntity] = None
    error: Optional[str] = None


class GenerateQRCodeUseCase:
    def __init__(
        self,
        url_validator: URLValidationService,
        settings_validator: QRSettingsValidationService,
        generator: QRCodeGenerator,
    ) -> None:
        self._url_validator = url_validator
        self._settings_validator = settings_validator
        self._generator = generator

    def execute(self, settings: QRSettingsEntity) -> GenerateQRResult:
        url_result = self._url_validator.validate(settings.url)
        if not url_result.valid:
            return GenerateQRResult(success=False, error=url_result.error)

        settings_result = self._settings_validator.validate(settings)
        if not settings_result.valid:
            return GenerateQRResult(success=False, error=settings_result.error)

        png_bytes = self._generator.generate(settings)
        qr = QRCodeEntity(settings=settings, image_data=png_bytes)
        return GenerateQRResult(success=True, qr=qr)


# ─────────────────────────────────────────────────────────────────────────────
# Export QR Code
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExportResult:
    success: bool
    path: Optional[Path] = None
    error: Optional[str] = None


class ExportQRCodeUseCase:
    def execute(
        self,
        qr: QRCodeEntity,
        destination: Path,
        format_key: str,
    ) -> ExportResult:
        exporter = EXPORTER_MAP.get(format_key.upper())
        if exporter is None:
            return ExportResult(success=False, error=f"Unknown format: {format_key}")
        try:
            # Ensure correct extension
            if not destination.suffix.lower() == exporter.extension:
                destination = destination.with_suffix(exporter.extension)
            exporter.export(qr.image_data, destination)
            return ExportResult(success=True, path=destination)
        except Exception as exc:
            return ExportResult(success=False, error=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# History Use Cases
# ─────────────────────────────────────────────────────────────────────────────

class SaveHistoryUseCase:
    def __init__(self, repo: HistoryRepository, generator: QRCodeGenerator) -> None:
        self._repo = repo
        self._generator = generator

    def execute(self, qr: QRCodeEntity) -> str:
        thumbnail = self._generator.generate_thumbnail(qr.image_data)
        return self._repo.save(qr, thumbnail)


class LoadHistoryUseCase:
    def __init__(self, repo: HistoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[HistoryItemEntity]:
        return self._repo.load_all()


class DeleteHistoryItemUseCase:
    def __init__(self, repo: HistoryRepository) -> None:
        self._repo = repo

    def execute(self, item_id: str) -> None:
        self._repo.delete(item_id)


class ClearHistoryUseCase:
    def __init__(self, repo: HistoryRepository) -> None:
        self._repo = repo

    def execute(self) -> None:
        self._repo.clear_all()


# ─────────────────────────────────────────────────────────────────────────────
# Clipboard
# ─────────────────────────────────────────────────────────────────────────────

class CopyToClipboardUseCase:
    def __init__(self, adapter: ClipboardAdapter) -> None:
        self._adapter = adapter

    def execute(self, qr: QRCodeEntity) -> None:
        self._adapter.copy_png(qr.image_data)
