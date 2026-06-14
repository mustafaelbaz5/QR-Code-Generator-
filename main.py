"""
Entry Point
Bootstraps the Qt application and shows the main window.
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.core.config import APP_NAME
from app.presentation.ui.main_window import MainWindow


def main() -> None:
    # High-DPI support (Qt 6 default)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")          # cross-platform baseline

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
