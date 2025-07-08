# gui/views/dashboard.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QFile, QTextStream
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget
# from .system_settings_view import SystemSettingsView # Tidak perlu lagi import SystemSettingsView di sini untuk logika penerusan app

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASV Control System")
        self.setGeometry(100, 100, 1600, 900)

        self.app = None
        self.current_theme = "dark" # Default theme is dark

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Header ---
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)

        # --- Content Area ---
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # Left Panel (Vehicle Control)
        self.control_panel = ControlPanel()
        self.content_layout.addWidget(self.control_panel, 1)

        # Center Widget (Map, Video, Settings)
        self.central_view = CentralWidget()
        self.content_layout.addWidget(self.central_view, 3)

        # Right Panel (Waypoints & Status)
        self.status_panel = StatusPanel()
        self.content_layout.addWidget(self.status_panel, 1)

    def set_application(self, app_instance):
        """Sets the QApplication instance for theme switching."""
        self.app = app_instance
        # <<< HAPUS BLOK KODE INI >>>
        # if hasattr(self.control_panel, 'settings_tabs'):
        #     for i in range(self.control_panel.settings_tabs.count()):
        #         widget = self.control_panel.settings_tabs.widget(i)
        #         if isinstance(widget, SystemSettingsView):
        #             widget.set_application_instance(self.app)
        #             break
        # <<< AKHIR HAPUS >>>


    def _create_header(self):
        """Creates the top header widget."""
        header_widget = QWidget()
        header_widget.setObjectName("Header")
        header_layout = QHBoxLayout(header_widget)

        title = QLabel("ASV Control System")

        status_connected = QLabel("Connected")
        status_connected.setObjectName("StatusLabel")
        status_connected.setProperty("connected", True)

        status_gps = QLabel("GPS: 12 Sats")
        status_gps.setObjectName("StatusLabel")
        status_gps.setProperty("connected", True)

        status_mode = QLabel("Auto Mode")
        status_mode.setObjectName("StatusLabel")
        status_mode.setProperty("connected", True)

        self.theme_toggle_button = QPushButton("Switch to Light Mode")
        self.theme_toggle_button.clicked.connect(self._toggle_theme)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_connected)
        header_layout.addWidget(status_gps)
        header_layout.addWidget(status_mode)
        header_layout.addWidget(self.theme_toggle_button)

        header_widget.setFixedHeight(60)

        return header_widget

    def _toggle_theme(self):
        """Toggles between dark and light themes and applies the stylesheet."""
        if not self.app:
            print("QApplication instance not set. Cannot toggle theme.")
            return

        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_toggle_button.setText("Switch to Dark Mode")
            stylesheet_path = "gui/resources/light_theme.qss"
        else:
            self.current_theme = "dark"
            self.theme_toggle_button.setText("Switch to Light Mode")
            stylesheet_path = "gui/resources/dark_theme.qss"

        qss_file = QFile(stylesheet_path)
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(qss_file)
            self.app.setStyleSheet(stream.readAll())
            qss_file.close()
            print(f"Switched to {self.current_theme} theme.")
        else:
            print(f"Error: Could not open stylesheet file: {stylesheet_path}")