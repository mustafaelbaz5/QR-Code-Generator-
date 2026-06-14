"""
Presentation Layer — Reusable Widgets
Self-contained, theme-agnostic UI components.
"""
from __future__ import annotations
import io

from PIL import Image
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
)

from app.domain.entities.entities import HistoryItemEntity


# ─────────────────────────────────────────────────────────────────────────────
# QR Preview Panel
# ─────────────────────────────────────────────────────────────────────────────

class QRPreviewWidget(QWidget):
    """Shows the generated QR image, with a placeholder when empty."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(240, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._show_placeholder()

    def set_image(self, png_bytes: bytes) -> None:
        qimg = _png_bytes_to_qimage(png_bytes)
        pixmap = QPixmap.fromImage(qimg).scaled(
            260, 260,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(pixmap)
        self._label.setText("")

    def clear(self) -> None:
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self._label.setPixmap(QPixmap())
        self._label.setText("QR preview will\nappear here")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #5A5A72; font-size: 14px;")


# ─────────────────────────────────────────────────────────────────────────────
# Color Picker Button
# ─────────────────────────────────────────────────────────────────────────────

class ColorButton(QPushButton):
    """A button that shows a color swatch and opens a color dialog on click."""

    color_changed = Signal(str)   # emits hex string e.g. "#FF0000"

    def __init__(self, color: str = "#000000", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(36, 36)
        self.setToolTip("Click to choose color")
        self._refresh()
        self.clicked.connect(self._pick_color)

    def color(self) -> str:
        return self._color

    def set_color(self, hex_color: str) -> None:
        self._color = hex_color
        self._refresh()

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._color}; "
            f"border: 2px solid #3A3A4A; border-radius: 6px; }}"
            f"QPushButton:hover {{ border-color: #6366F1; }}"
        )

    def _pick_color(self) -> None:
        from PySide6.QtWidgets import QColorDialog
        dlg = QColorDialog(QColor(self._color), self)
        if dlg.exec():
            chosen = dlg.selectedColor().name()
            self._color = chosen
            self._refresh()
            self.color_changed.emit(chosen)


# ─────────────────────────────────────────────────────────────────────────────
# History Item Widget
# ─────────────────────────────────────────────────────────────────────────────

class HistoryItemWidget(QFrame):
    """Compact card for one history entry in the sidebar."""

    clicked = Signal(str)          # emits item id
    delete_requested = Signal(str) # emits item id

    def __init__(self, item: HistoryItemEntity, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(68)
        self.setObjectName("historyCard")
        self.setStyleSheet("""
            QFrame#historyCard {
                border-radius: 8px;
                border: 1px solid transparent;
                margin: 1px 4px;
            }
            QFrame#historyCard:hover {
                border-color: #6366F1;
                background-color: #1E1E28;
            }
        """)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(48, 48)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if item.thumbnail_data:
            qimg = _png_bytes_to_qimage(item.thumbnail_data)
            thumb_label.setPixmap(
                QPixmap.fromImage(qimg).scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # URL text
        url_label = QLabel(item.url)
        url_label.setWordWrap(False)
        url_label.setStyleSheet("font-size: 11px; color: #9191A8;")
        url_label.setMaximumWidth(150)

        date_label = QLabel(item.created_at.strftime("%b %d, %H:%M"))
        date_label.setStyleSheet("font-size: 10px; color: #5A5A72;")

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setProperty("ghost", True)
        del_btn.setToolTip("Remove from history")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._item.id))
        del_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #5A5A72; border: none; font-size: 11px; }"
            "QPushButton:hover { color: #EF4444; }"
        )

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.addWidget(url_label)
        info_col.addWidget(date_label)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 8, 8, 8)
        row.setSpacing(8)
        row.addWidget(thumb_label)
        row.addLayout(info_col)
        row.addStretch()
        row.addWidget(del_btn)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._item.id)
        super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# History Sidebar
# ─────────────────────────────────────────────────────────────────────────────

class HistorySidebar(QWidget):
    """Scrollable list of HistoryItemWidgets."""

    item_selected = Signal(str)
    item_deleted = Signal(str)
    clear_all_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(230)

        # Header
        header = QLabel("History")
        header.setProperty("heading", True)
        header.setContentsMargins(12, 0, 0, 0)

        clear_btn = QPushButton("Clear all")
        clear_btn.setProperty("ghost", True)
        clear_btn.setFixedHeight(24)
        clear_btn.clicked.connect(self.clear_all_requested)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(clear_btn)

        # Scroll area for items
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._inner = QWidget()
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(2)
        self._inner_layout.addStretch()

        self._scroll.setWidget(self._inner)

        self._empty_label = QLabel("No history yet")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #5A5A72; font-size: 12px; padding: 20px;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 16, 0, 0)
        root.setSpacing(8)
        root.addLayout(header_row)
        root.addWidget(self._scroll)

        self._widgets: dict[str, HistoryItemWidget] = {}

    def populate(self, items: list[HistoryItemEntity]) -> None:
        # Clear existing
        for w in self._widgets.values():
            self._inner_layout.removeWidget(w)
            w.deleteLater()
        self._widgets.clear()

        if not items:
            self._inner_layout.insertWidget(0, self._empty_label)
            return

        self._empty_label.setParent(None)

        for item in items:
            widget = HistoryItemWidget(item)
            widget.clicked.connect(self.item_selected)
            widget.delete_requested.connect(self.item_deleted)
            self._inner_layout.insertWidget(self._inner_layout.count() - 1, widget)
            self._widgets[item.id] = widget

    def remove_item(self, item_id: str) -> None:
        if item_id in self._widgets:
            w = self._widgets.pop(item_id)
            self._inner_layout.removeWidget(w)
            w.deleteLater()


# ─────────────────────────────────────────────────────────────────────────────
# Status Badge
# ─────────────────────────────────────────────────────────────────────────────

class StatusBadge(QLabel):
    """Temporarily visible inline status message."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clear)
        self.setVisible(False)

    def show_success(self, text: str, duration_ms: int = 3000) -> None:
        self._show(text, "#22C55E", duration_ms)

    def show_error(self, text: str, duration_ms: int = 4000) -> None:
        self._show(text, "#EF4444", duration_ms)

    def show_info(self, text: str, duration_ms: int = 2500) -> None:
        self._show(text, "#6366F1", duration_ms)

    def _show(self, text: str, color: str, duration_ms: int) -> None:
        self.setText(text)
        self.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 500;"
        )
        self.setVisible(True)
        self._timer.start(duration_ms)

    def clear(self) -> None:  # type: ignore[override]
        self.setText("")
        self.setVisible(False)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _png_bytes_to_qimage(png_bytes: bytes) -> QImage:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    return QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)


def labeled_row(label_text: str, widget: QWidget, spacing: int = 8) -> QHBoxLayout:
    """Utility: returns an HBoxLayout with a label on the left and widget on the right."""
    lbl = QLabel(label_text)
    lbl.setMinimumWidth(90)
    lbl.setStyleSheet("color: #9191A8; font-size: 12px;")
    row = QHBoxLayout()
    row.setSpacing(spacing)
    row.addWidget(lbl)
    row.addWidget(widget)
    return row


def section_divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    return line
