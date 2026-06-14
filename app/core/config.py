"""
Core — Application Configuration
Single source of truth for runtime paths and defaults.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path


def _app_data_dir() -> Path:
    """
    Return a writable directory for app data.
    On Windows uses %APPDATA%, on macOS ~/Library/Application Support,
    elsewhere ~/.local/share.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    data_dir = base / "QRCodeGenerator"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


APP_NAME = "QR Code Generator"
APP_VERSION = "1.0.0"
APP_DATA_DIR: Path = _app_data_dir()
DB_PATH: Path = APP_DATA_DIR / "history.db"
DEFAULT_EXPORT_DIR: Path = Path.home() / "Downloads"
