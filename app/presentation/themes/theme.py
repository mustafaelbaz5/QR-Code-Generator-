"""
Presentation Layer — Design System / Theme
One source of truth for every color, radius, and spacing value.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    # Backgrounds
    bg_primary: str
    bg_secondary: str
    bg_surface: str
    bg_input: str

    # Borders
    border: str
    border_focus: str

    # Accent
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_text: str      # text ON accent button

    # Text
    text_primary: str
    text_secondary: str
    text_placeholder: str
    text_disabled: str

    # Semantic
    success: str
    warning: str
    error: str

    # Sidebar
    sidebar_bg: str
    sidebar_item_hover: str
    sidebar_item_selected: str


DARK = ColorPalette(
    bg_primary="#0F0F13",
    bg_secondary="#17171D",
    bg_surface="#1E1E26",
    bg_input="#13131A",

    border="#2E2E3A",
    border_focus="#6366F1",

    accent="#6366F1",
    accent_hover="#818CF8",
    accent_pressed="#4F46E5",
    accent_text="#FFFFFF",

    text_primary="#F1F1F8",
    text_secondary="#9191A8",
    text_placeholder="#5A5A72",
    text_disabled="#3A3A4A",

    success="#22C55E",
    warning="#F59E0B",
    error="#EF4444",

    sidebar_bg="#12121A",
    sidebar_item_hover="#1E1E28",
    sidebar_item_selected="#252532",
)

LIGHT = ColorPalette(
    bg_primary="#F5F5FA",
    bg_secondary="#FFFFFF",
    bg_surface="#FFFFFF",
    bg_input="#F0F0F7",

    border="#E2E2EE",
    border_focus="#6366F1",

    accent="#6366F1",
    accent_hover="#818CF8",
    accent_pressed="#4F46E5",
    accent_text="#FFFFFF",

    text_primary="#1A1A2E",
    text_secondary="#6B6B88",
    text_placeholder="#ADADC8",
    text_disabled="#D0D0E0",

    success="#16A34A",
    warning="#D97706",
    error="#DC2626",

    sidebar_bg="#EEEEF8",
    sidebar_item_hover="#E0E0F0",
    sidebar_item_selected="#D8D8F0",
)


def build_stylesheet(palette: ColorPalette) -> str:
    p = palette
    return f"""
/* ── Global ──────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
    color: {p.text_primary};
    outline: none;
}}

QWidget {{
    background-color: {p.bg_primary};
}}

QMainWindow {{
    background-color: {p.bg_primary};
}}

/* ── Scroll Bars ─────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p.border};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{ height: 6px; background: transparent; }}
QScrollBar::handle:horizontal {{
    background: {p.border};
    border-radius: 3px;
}}

/* ── Labels ──────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {p.text_primary};
}}
QLabel[secondary="true"] {{
    color: {p.text_secondary};
    font-size: 12px;
}}
QLabel[heading="true"] {{
    font-size: 15px;
    font-weight: 600;
    color: {p.text_primary};
}}

/* ── Line Edits ──────────────────────────────────────────────── */
QLineEdit {{
    background-color: {p.bg_input};
    border: 1.5px solid {p.border};
    border-radius: 8px;
    padding: 8px 12px;
    color: {p.text_primary};
    selection-background-color: {p.accent};
}}
QLineEdit:focus {{
    border-color: {p.border_focus};
    background-color: {p.bg_secondary};
}}
QLineEdit:disabled {{
    color: {p.text_disabled};
    border-color: {p.border};
}}
QLineEdit[error="true"] {{
    border-color: {p.error};
}}

/* ── Push Buttons ────────────────────────────────────────────── */
QPushButton {{
    background-color: {p.accent};
    color: {p.accent_text};
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {p.accent_hover};
}}
QPushButton:pressed {{
    background-color: {p.accent_pressed};
}}
QPushButton:disabled {{
    background-color: {p.border};
    color: {p.text_disabled};
}}
QPushButton[secondary="true"] {{
    background-color: {p.bg_surface};
    color: {p.text_primary};
    border: 1.5px solid {p.border};
}}
QPushButton[secondary="true"]:hover {{
    border-color: {p.accent};
    color: {p.accent};
}}
QPushButton[danger="true"] {{
    background-color: transparent;
    color: {p.error};
    border: 1.5px solid {p.error};
}}
QPushButton[danger="true"]:hover {{
    background-color: {p.error};
    color: white;
}}
QPushButton[ghost="true"] {{
    background-color: transparent;
    color: {p.text_secondary};
    border: none;
    padding: 6px 12px;
    font-weight: 400;
}}
QPushButton[ghost="true"]:hover {{
    color: {p.accent};
    background-color: {p.sidebar_item_hover};
    border-radius: 6px;
}}

/* ── Combo Box ───────────────────────────────────────────────── */
QComboBox {{
    background-color: {p.bg_input};
    border: 1.5px solid {p.border};
    border-radius: 8px;
    padding: 7px 12px;
    color: {p.text_primary};
    min-width: 100px;
}}
QComboBox:focus {{
    border-color: {p.border_focus};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {p.bg_surface};
    border: 1.5px solid {p.border};
    border-radius: 8px;
    selection-background-color: {p.accent};
    outline: none;
}}

/* ── Sliders ─────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {p.border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p.accent};
    border: none;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {p.accent};
    border-radius: 2px;
}}

/* ── Check Box ───────────────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {p.text_primary};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {p.border};
    border-radius: 4px;
    background: {p.bg_input};
}}
QCheckBox::indicator:checked {{
    background: {p.accent};
    border-color: {p.accent};
}}

/* ── Tooltips ────────────────────────────────────────────────── */
QToolTip {{
    background-color: {p.bg_surface};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 4px 8px;
}}

/* ── Status Bar ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: {p.bg_secondary};
    color: {p.text_secondary};
    border-top: 1px solid {p.border};
    font-size: 12px;
    padding: 0 8px;
}}

/* ── Separator ───────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {p.border};
}}
"""
