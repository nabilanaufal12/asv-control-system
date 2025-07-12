# gui/views/dashboard.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton, QSplitter
from PyQt5.QtCore import Qt, QFile, QTextStream

from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget
from core.serial_handler import SerialHandler

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASV Control System")
        self.setGeometry(100, 100, 1600, 900)

        self.app = None
        self.current_theme = "dark"
        self.serial_handler = SerialHandler()
        self.statusBar().showMessage("Welcome to ASV Control System!", 5000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.header = self._create_header()
        self.main_layout.addWidget(self.header)

        self.control_panel = ControlPanel(parent=self, serial_handler=self.serial_handler)
        self.central_view = CentralWidget(parent=self)
        self.status_panel = StatusPanel(parent=self)
        
        self.control_panel.tab_connection_settings.set_serial_handler(self.serial_handler)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.central_view)
        splitter.addWidget(self.status_panel)
        splitter.setSizes([320, 960, 320])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(2, False)
        self.main_layout.addWidget(splitter)

        self.connect_signals()

    def connect_signals(self):
        """Fungsi terpusat untuk mengatur semua koneksi sinyal-slot."""
        self.central_view.tab_video.degree_changed.connect(self.control_panel.set_servo_from_yolo)
        self.central_view.tab_video.degree_changed.connect(self.status_panel.update_auto_steering_degree)
        self.control_panel.connection_status_changed.connect(self.update_header_connection_status)
        self.control_panel.mode_changed.connect(self.update_header_mode_status)
        self.status_panel.message_to_show.connect(self.show_temporary_message)
        
        # === PERBAIKAN: Hubungkan sinyal pesan dari ControlPanel ===
        self.control_panel.message_to_show.connect(self.show_temporary_message)
        
        print("Semua sinyal utama telah berhasil terhubung.")

    def set_application(self, app_instance):
        self.app = app_instance

    def _create_header(self):
        header_widget = QWidget()
        header_widget.setObjectName("Header")
        header_layout = QHBoxLayout(header_widget)
        title = QLabel("ASV Control System")
        self.header_status_connection = QLabel("Disconnected")
        self.header_status_connection.setObjectName("StatusLabel")
        self.header_status_connection.setProperty("connected", False)
        self.header_status_gps = QLabel("GPS: 0 Sats")
        self.header_status_gps.setObjectName("StatusLabel")
        self.header_status_gps.setProperty("connected", False)
        self.header_status_mode = QLabel("Manual Mode")
        self.header_status_mode.setObjectName("StatusLabel")
        self.header_status_mode.setProperty("connected", False)
        self.theme_toggle_button = QPushButton("Switch to Light Mode")
        self.theme_toggle_button.clicked.connect(self._toggle_theme)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.header_status_connection)
        header_layout.addWidget(self.header_status_gps)
        header_layout.addWidget(self.header_status_mode)
        header_layout.addWidget(self.theme_toggle_button)
        header_widget.setFixedHeight(60)
        return header_widget

    def handle_received_data(self, data):
        print(f"[ESP32 -> GUI]: {data}")

    def update_header_connection_status(self, is_connected, message):
        self.header_status_connection.setText(message)
        self.header_status_connection.setProperty("connected", is_connected)
        self.style().polish(self.header_status_connection)
        
        if is_connected and self.serial_handler.reader_thread:
            try:
                self.serial_handler.reader_thread.data_received.disconnect(self.handle_received_data)
            except TypeError:
                pass
            self.serial_handler.reader_thread.data_received.connect(self.handle_received_data)
        
        print(f"Header status diupdate: {message}")

    def update_header_mode_status(self, is_auto_mode):
        mode_text = "Auto Mode" if is_auto_mode else "Manual Mode"
        self.header_status_mode.setText(mode_text)
        self.header_status_mode.setProperty("connected", is_auto_mode)
        self.style().polish(self.header_status_mode)
        self.show_temporary_message(f"Mode switched to {mode_text.replace(' Mode', '')}", 3000)
        print(f"Header status diupdate: {mode_text}")

    def show_temporary_message(self, message, duration=3000):
        self.statusBar().showMessage(message, duration)

    def _toggle_theme(self):
        if not self.app: return
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_toggle_button.setText("Switch to Dark Mode")
            stylesheet_path = "gui/resources/light_theme.qss"
        else:
            self.current_theme = "dark"
            self.theme_toggle_button.setText("Switch to Light Mode")
            stylesheet_path = "gui/resources/dark_theme.qss"
        try:
            with open(stylesheet_path, "r") as f:
                self.app.setStyleSheet(f.read())
        except FileNotFoundError:
            error_msg = f"Error: Gagal membuka stylesheet {stylesheet_path}"
            print(error_msg)
            self.show_temporary_message(error_msg, 5000)

    def closeEvent(self, event):
        print("Closing application, disconnecting serial port...")
        self.serial_handler.disconnect()
        event.accept()
