"""PhreeFit application entry point.

This file remains named ``PhreeFit.py`` so existing launch and packaging scripts
can be adapted by changing only the source directory from ``src`` to ``src_new``.
"""

import multiprocessing
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

if __package__:
    from .main_window import MainWindow
    from .version import __version__
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src_new.main_window import MainWindow
    from src_new.version import __version__


def main():
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setOrganizationName("PhreeFit")
    app.setApplicationName("PhreeFit")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
