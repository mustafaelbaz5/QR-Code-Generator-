"""
Core — Dependency Injection Container
Single place where concrete classes are wired to interfaces.
No business logic here — only object graph construction.
"""
from __future__ import annotations
from functools import cached_property

from app.core.config import DB_PATH
from app.domain.services.validation import URLValidationService, QRSettingsValidationService
from app.infrastructure.qr.generator import QRCodeGenerator
from app.infrastructure.storage.history_repository import HistoryRepository
from app.infrastructure.clipboard.clipboard import ClipboardAdapter
from app.application.use_cases.use_cases import (
    ValidateURLUseCase,
    GenerateQRCodeUseCase,
    ExportQRCodeUseCase,
    SaveHistoryUseCase,
    LoadHistoryUseCase,
    DeleteHistoryItemUseCase,
    ClearHistoryUseCase,
    CopyToClipboardUseCase,
)


class Container:
    # ── Infrastructure ──────────────────────────────────────────────────────

    @cached_property
    def qr_generator(self) -> QRCodeGenerator:
        return QRCodeGenerator()

    @cached_property
    def history_repository(self) -> HistoryRepository:
        return HistoryRepository(DB_PATH)

    @cached_property
    def clipboard_adapter(self) -> ClipboardAdapter:
        return ClipboardAdapter()

    # ── Domain Services ──────────────────────────────────────────────────────

    @cached_property
    def url_validator(self) -> URLValidationService:
        return URLValidationService()

    @cached_property
    def settings_validator(self) -> QRSettingsValidationService:
        return QRSettingsValidationService()

    # ── Use Cases ────────────────────────────────────────────────────────────

    @cached_property
    def validate_url(self) -> ValidateURLUseCase:
        return ValidateURLUseCase(self.url_validator)

    @cached_property
    def generate_qr(self) -> GenerateQRCodeUseCase:
        return GenerateQRCodeUseCase(
            self.url_validator,
            self.settings_validator,
            self.qr_generator,
        )

    @cached_property
    def export_qr(self) -> ExportQRCodeUseCase:
        return ExportQRCodeUseCase()

    @cached_property
    def save_history(self) -> SaveHistoryUseCase:
        return SaveHistoryUseCase(self.history_repository, self.qr_generator)

    @cached_property
    def load_history(self) -> LoadHistoryUseCase:
        return LoadHistoryUseCase(self.history_repository)

    @cached_property
    def delete_history_item(self) -> DeleteHistoryItemUseCase:
        return DeleteHistoryItemUseCase(self.history_repository)

    @cached_property
    def clear_history(self) -> ClearHistoryUseCase:
        return ClearHistoryUseCase(self.history_repository)

    @cached_property
    def copy_to_clipboard(self) -> CopyToClipboardUseCase:
        return CopyToClipboardUseCase(self.clipboard_adapter)


# Global singleton — import this everywhere
container = Container()
