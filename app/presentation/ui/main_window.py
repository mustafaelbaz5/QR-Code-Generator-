"""
Presentation Layer — Main Window
Purely orchestrates widgets and delegates everything to use cases.
Zero business logic lives here.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSlider,
    QCheckBox, QFrame, QStatusBar, QSizePolicy,
    QFileDialog, QMessageBox, QApplication,
)

from app.core.config import APP_NAME, APP_VERSION, DEFAULT_EXPORT_DIR
from app.core.di_container import container
from app.domain.entities.entities import (
    QRSettingsEntity, QRCodeEntity, ErrorCorrectionLevel, HistoryItemEntity,
)
from app.presentation.themes.theme import DARK, LIGHT, build_stylesheet
from app.presentation.widgets.widgets import (
    QRPreviewWidget, ColorButton, HistorySidebar, StatusBadge,
    labeled_row, section_divider,
)


# ─────────────────────────────────────────────────────────────────────────────
# Background worker — keeps UI responsive during generation
# ─────────────────────────────────────────────────────────────────────────────

class _GenerateWorker(QObject):
    finished = Signal(object)   # QRCodeEntity | None
    error = Signal(str)

    def __init__(self, settings: QRSettingsEntity) -> None:
        super().__init__()
        self._settings = settings

    def run(self) -> None:
        result = container.generate_qr.execute(self._settings)
        if result.success and result.qr:
            self.finished.emit(result.qr)
        else:
            self.error.emit(result.error or "Unknown error")


# ─────────────────────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._current_qr: QRCodeEntity | None = None
        self._dark_mode = True
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(400)
        self._debounce_timer.timeout.connect(self._trigger_generate)
        self._thread: QThread | None = None

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 620)
        self.resize(1060, 680)

        self._build_ui()
        self._apply_theme()
        self._load_history()
        self.setAcceptDrops(True)

        # Keyboard shortcut: Ctrl+G = Generate
        QShortcut(QKeySequence("Ctrl+G"), self, activated=self._trigger_generate)
        # Ctrl+C = Copy
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=self._copy_to_clipboard)

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        self._sidebar = HistorySidebar()
        self._sidebar.item_selected.connect(self._on_history_selected)
        self._sidebar.item_deleted.connect(self._on_history_delete)
        self._sidebar.clear_all_requested.connect(self._on_clear_history)

        sidebar_wrapper = QWidget()
        sidebar_wrapper.setFixedWidth(240)
        sidebar_wrapper.setObjectName("sidebar")
        sw_layout = QVBoxLayout(sidebar_wrapper)
        sw_layout.setContentsMargins(8, 0, 8, 16)
        sw_layout.addWidget(self._sidebar)

        # ── Centre column ─────────────────────────────────────────────────────
        centre = QWidget()
        centre_layout = QVBoxLayout(centre)
        centre_layout.setContentsMargins(28, 28, 28, 16)
        centre_layout.setSpacing(20)

        # App title row
        title_row = QHBoxLayout()
        app_title = QLabel(APP_NAME)
        app_title.setStyleSheet("font-size: 22px; font-weight: 700; letter-spacing: -0.5px;")
        self._theme_btn = QPushButton("☀ Light")
        self._theme_btn.setProperty("ghost", True)
        self._theme_btn.clicked.connect(self._toggle_theme)
        title_row.addWidget(app_title)
        title_row.addStretch()
        title_row.addWidget(self._theme_btn)
        centre_layout.addLayout(title_row)

        # ── URL input ─────────────────────────────────────────────────────────
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://example.com  — or drag & drop a URL here")
        self._url_input.setMinimumHeight(44)
        self._url_input.textChanged.connect(self._on_url_changed)
        self._url_input.returnPressed.connect(self._trigger_generate)

        self._url_error_label = QLabel()
        self._url_error_label.setStyleSheet("color: #EF4444; font-size: 11px;")
        self._url_error_label.setVisible(False)

        url_col = QVBoxLayout()
        url_col.setSpacing(4)
        url_col.addWidget(QLabel("URL", styleSheet="font-weight: 600; font-size: 12px;"))
        url_col.addWidget(self._url_input)
        url_col.addWidget(self._url_error_label)
        centre_layout.addLayout(url_col)

        # ── Main content row (preview + settings) ─────────────────────────────
        content_row = QHBoxLayout()
        content_row.setSpacing(28)

        # Preview
        preview_col = QVBoxLayout()
        preview_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        self._preview = QRPreviewWidget()
        self._preview.setObjectName("previewCard")
        self._status_badge = StatusBadge()
        preview_col.addWidget(preview_label)
        preview_col.addWidget(self._preview)
        preview_col.addWidget(self._status_badge)
        preview_col.addStretch()

        content_row.addLayout(preview_col)

        # Vertical separator
        sep = section_divider()
        sep.setFrameShape(QFrame.Shape.VLine)
        content_row.addWidget(sep)

        # Settings panel
        settings_col = QVBoxLayout()
        settings_col.setSpacing(14)
        settings_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-weight: 600; font-size: 12px;")
        settings_col.addWidget(settings_title)

        # Error correction
        self._ec_combo = QComboBox()
        for ec in ErrorCorrectionLevel:
            self._ec_combo.addItem(
                {"L": "L — Low (7%)", "M": "M — Medium (15%)",
                 "Q": "Q — Quartile (25%)", "H": "H — High (30%)"}[ec.value],
                ec.value,
            )
        self._ec_combo.setCurrentIndex(1)
        self._ec_combo.currentIndexChanged.connect(self._schedule_generate)
        settings_col.addLayout(labeled_row("Error correction", self._ec_combo))

        # Size slider
        self._size_slider = QSlider(Qt.Orientation.Horizontal)
        self._size_slider.setRange(100, 1000)
        self._size_slider.setValue(300)
        self._size_slider.setTickInterval(100)
        self._size_slider.valueChanged.connect(self._on_size_changed)
        self._size_value_label = QLabel("300 px")
        self._size_value_label.setFixedWidth(52)
        self._size_value_label.setStyleSheet("color: #9191A8; font-size: 12px;")
        size_row = QHBoxLayout()
        size_row.addWidget(self._size_slider)
        size_row.addWidget(self._size_value_label)
        settings_col.addLayout(labeled_row("Image size", self._size_slider_wrapper(size_row)))

        # Box size slider
        self._box_slider = QSlider(Qt.Orientation.Horizontal)
        self._box_slider.setRange(1, 30)
        self._box_slider.setValue(10)
        self._box_slider.valueChanged.connect(self._on_box_changed)
        self._box_value_label = QLabel("10")
        self._box_value_label.setFixedWidth(32)
        self._box_value_label.setStyleSheet("color: #9191A8; font-size: 12px;")
        box_row = QHBoxLayout()
        box_row.addWidget(self._box_slider)
        box_row.addWidget(self._box_value_label)
        settings_col.addLayout(labeled_row("Box size", self._size_slider_wrapper(box_row)))

        # Margin slider
        self._margin_slider = QSlider(Qt.Orientation.Horizontal)
        self._margin_slider.setRange(0, 10)
        self._margin_slider.setValue(4)
        self._margin_slider.valueChanged.connect(self._on_margin_changed)
        self._margin_value_label = QLabel("4")
        self._margin_value_label.setFixedWidth(32)
        self._margin_value_label.setStyleSheet("color: #9191A8; font-size: 12px;")
        margin_row = QHBoxLayout()
        margin_row.addWidget(self._margin_slider)
        margin_row.addWidget(self._margin_value_label)
        settings_col.addLayout(labeled_row("Margin", self._size_slider_wrapper(margin_row)))

        settings_col.addWidget(section_divider())

        # Colors
        self._fg_btn = ColorButton("#000000")
        self._fg_btn.color_changed.connect(self._schedule_generate)
        settings_col.addLayout(labeled_row("QR color", self._fg_btn))

        self._bg_btn = ColorButton("#FFFFFF")
        self._bg_btn.color_changed.connect(self._schedule_generate)
        settings_col.addLayout(labeled_row("Background", self._bg_btn))

        # Quiet zone toggle
        self._quiet_zone_cb = QCheckBox("Add quiet zone")
        self._quiet_zone_cb.setChecked(True)
        self._quiet_zone_cb.stateChanged.connect(self._schedule_generate)
        settings_col.addWidget(self._quiet_zone_cb)

        settings_col.addStretch()
        content_row.addLayout(settings_col)
        centre_layout.addLayout(content_row)

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._generate_btn = QPushButton("⚡  Generate")
        self._generate_btn.setMinimumHeight(40)
        self._generate_btn.clicked.connect(self._trigger_generate)

        self._copy_btn = QPushButton("⎘  Copy")
        self._copy_btn.setProperty("secondary", True)
        self._copy_btn.setMinimumHeight(40)
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)

        for fmt in ("PNG", "JPG", "PDF", "SVG"):
            btn = QPushButton(f"↓ {fmt}")
            btn.setProperty("secondary", True)
            btn.setMinimumHeight(40)
            btn.setToolTip(f"Export as {fmt}")
            btn.setEnabled(False)
            btn.clicked.connect(lambda _, f=fmt: self._export(f))
            setattr(self, f"_export_{fmt.lower()}_btn", btn)
            btn_row.addWidget(btn)

        btn_row.insertWidget(0, self._generate_btn)
        btn_row.insertWidget(1, self._copy_btn)
        btn_row.addStretch()
        centre_layout.addLayout(btn_row)

        # ── Assemble root ─────────────────────────────────────────────────────
        root.addWidget(sidebar_wrapper)

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFixedWidth(1)
        root.addWidget(vline)

        root.addWidget(centre, stretch=1)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.showMessage(f"{APP_NAME} {APP_VERSION} — Ready")
        self.setStatusBar(self._status_bar)

    def _size_slider_wrapper(self, inner_layout: QHBoxLayout) -> QWidget:
        """Wraps a layout into a QWidget for use in labeled_row."""
        w = QWidget()
        w.setLayout(inner_layout)
        return w

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        palette = DARK if self._dark_mode else LIGHT
        self.setStyleSheet(build_stylesheet(palette))
        # Sidebar background
        sidebar_wrapper = self.findChild(QWidget, "sidebar")
        if sidebar_wrapper:
            sidebar_wrapper.setStyleSheet(
                f"QWidget#sidebar {{ background-color: {palette.sidebar_bg}; }}"
            )
        # Preview card border
        preview_card = self.findChild(QWidget, "previewCard")
        if preview_card:
            preview_card.setStyleSheet(
                f"QWidget#previewCard {{ "
                f"background-color: {palette.bg_surface}; "
                f"border: 1.5px solid {palette.border}; "
                f"border-radius: 12px; padding: 16px; }}"
            )

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        self._theme_btn.setText("☀ Light" if self._dark_mode else "🌙 Dark")
        self._apply_theme()

    # ── History ───────────────────────────────────────────────────────────────

    def _load_history(self) -> None:
        items = container.load_history.execute()
        self._sidebar.populate(items)
        self._history_items: dict[str, HistoryItemEntity] = {i.id: i for i in items}

    def _on_history_selected(self, item_id: str) -> None:
        item = self._history_items.get(item_id)
        if not item:
            return
        # Restore settings into UI
        self._url_input.blockSignals(True)
        self._url_input.setText(item.url)
        self._url_input.blockSignals(False)
        # Trigger fresh generation with restored settings
        ec_idx = {"L": 0, "M": 1, "Q": 2, "H": 3}.get(item.error_correction, 1)
        self._ec_combo.setCurrentIndex(ec_idx)
        self._size_slider.setValue(item.image_size)
        self._fg_btn.set_color(item.fg_color)
        self._bg_btn.set_color(item.bg_color)
        self._trigger_generate()

    def _on_history_delete(self, item_id: str) -> None:
        container.delete_history_item.execute(item_id)
        self._sidebar.remove_item(item_id)
        self._history_items.pop(item_id, None)

    def _on_clear_history(self) -> None:
        reply = QMessageBox.question(
            self, "Clear history",
            "Remove all history entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            container.clear_history.execute()
            self._load_history()

    # ── URL input ─────────────────────────────────────────────────────────────

    def _on_url_changed(self, text: str) -> None:
        result = container.validate_url.execute(text)
        if text and not result.valid:
            self._url_input.setProperty("error", True)
            self._url_input.style().unpolish(self._url_input)
            self._url_input.style().polish(self._url_input)
            self._url_error_label.setText(result.error or "")
            self._url_error_label.setVisible(True)
        else:
            self._url_input.setProperty("error", False)
            self._url_input.style().unpolish(self._url_input)
            self._url_input.style().polish(self._url_input)
            self._url_error_label.setVisible(False)
            if result.valid:
                self._debounce_timer.start()

    # ── Slider value labels ───────────────────────────────────────────────────

    def _on_size_changed(self, value: int) -> None:
        self._size_value_label.setText(f"{value} px")
        self._schedule_generate()

    def _on_box_changed(self, value: int) -> None:
        self._box_value_label.setText(str(value))
        self._schedule_generate()

    def _on_margin_changed(self, value: int) -> None:
        self._margin_value_label.setText(str(value))
        self._schedule_generate()

    def _schedule_generate(self, *_) -> None:
        """Start debounce; called when any setting changes."""
        url = self._url_input.text().strip()
        if url:
            self._debounce_timer.start()

    # ── Generation ────────────────────────────────────────────────────────────

    def _build_settings(self) -> QRSettingsEntity:
        ec_value = self._ec_combo.currentData()
        return QRSettingsEntity(
            url=self._url_input.text().strip(),
            fg_color=self._fg_btn.color(),
            bg_color=self._bg_btn.color(),
            box_size=self._box_slider.value(),
            border=self._margin_slider.value(),
            error_correction=ErrorCorrectionLevel(ec_value),
            add_quiet_zone=self._quiet_zone_cb.isChecked(),
            image_size=self._size_slider.value(),
        )

    def _trigger_generate(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        settings = self._build_settings()
        url_check = container.validate_url.execute(settings.url)
        if not url_check.valid:
            return

        self._generate_btn.setEnabled(False)
        self._generate_btn.setText("⏳  Generating…")
        self._status_bar.showMessage("Generating QR code…")

        self._worker = _GenerateWorker(settings)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_generate_success)
        self._worker.error.connect(self._on_generate_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._reset_generate_btn)
        self._thread.start()

    def _on_generate_success(self, qr: QRCodeEntity) -> None:
        self._current_qr = qr
        self._preview.set_image(qr.image_data)
        self._set_export_buttons_enabled(True)
        self._copy_btn.setEnabled(True)
        self._status_bar.showMessage("QR code generated successfully ✓", 4000)
        self._status_badge.show_success("Generated ✓")

        # Persist to history
        item_id = container.save_history.execute(qr)
        self._load_history()

    def _on_generate_error(self, error: str) -> None:
        self._status_bar.showMessage(f"Error: {error}", 5000)
        self._status_badge.show_error(error)

    def _reset_generate_btn(self) -> None:
        self._generate_btn.setEnabled(True)
        self._generate_btn.setText("⚡  Generate")

    def _set_export_buttons_enabled(self, enabled: bool) -> None:
        for fmt in ("png", "jpg", "pdf", "svg"):
            btn: QPushButton = getattr(self, f"_export_{fmt}_btn")
            btn.setEnabled(enabled)

    # ── Export ────────────────────────────────────────────────────────────────

    def _export(self, fmt: str) -> None:
        if not self._current_qr:
            return
        ext = {"PNG": ".png", "JPG": ".jpg", "PDF": ".pdf", "SVG": ".svg"}[fmt]
        default_name = f"qrcode{ext}"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {fmt}",
            str(DEFAULT_EXPORT_DIR / default_name),
            f"{fmt} Files (*{ext})",
        )
        if not path_str:
            return
        result = container.export_qr.execute(self._current_qr, Path(path_str), fmt)
        if result.success:
            self._status_badge.show_success(f"Saved as {fmt} ✓")
            self._status_bar.showMessage(f"Exported to {result.path}", 5000)
        else:
            self._status_badge.show_error(f"Export failed: {result.error}")

    # ── Clipboard ─────────────────────────────────────────────────────────────

    def _copy_to_clipboard(self) -> None:
        if not self._current_qr:
            return
        container.copy_to_clipboard.execute(self._current_qr)
        self._status_badge.show_info("Copied to clipboard")
        self._status_bar.showMessage("QR image copied to clipboard", 3000)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            url = mime.urls()[0].toString()
        elif mime.hasText():
            url = mime.text().strip()
        else:
            return
        self._url_input.setText(url)
        self._trigger_generate()
