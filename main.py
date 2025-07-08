# main.py

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream
from gui.views.dashboard import DashboardWindow

def load_stylesheet(app, stylesheet_path):
    """Loads a QSS stylesheet from the given path and applies it to the application."""
    qss_file = QFile(stylesheet_path)
    if qss_file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(qss_file)
        app.setStyleSheet(stream.readAll())
        qss_file.close()
        print(f"Loaded stylesheet: {stylesheet_path}")
    else:
        print(f"Error: Could not open stylesheet file: {stylesheet_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initial stylesheet (e.g., dark mode)
    load_stylesheet(app, "gui/resources/dark_theme.qss")

    window = DashboardWindow()
    window.show()

    # Pass the app instance to the dashboard for theme switching in header
    window.set_application(app)

    sys.exit(app.exec_())