# gui/views/dashboard.py

# === PERBAIKAN: Tambahkan QMainWindow dan widget lain yang dibutuhkan ke daftar impor ===
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QLabel, 
                             QVBoxLayout, QPushButton, QSplitter)
from PyQt5.QtCore import Qt, QFile, QTextStream, QTimer

# --- Impor Kustom ---
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget
from core.navigation import haversine, calculate_bearing
from core.pid_controller import PIDController
from core.serial_handler import SerialHandler


class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (semua kode __init__ Anda yang sudah ada hingga bagian timer) ...
        self.setWindowTitle("ASV Control System")
        self.setGeometry(100, 100, 1600, 900)
        self.app = None
        self.current_theme = "dark"
        self.serial_handler = SerialHandler()
        self.navigation_mode = "MANUAL"
        self.current_lat = 0.0
        self.current_lon = 0.0
        self.current_heading = 0.0
        self.waypoints = []
        self.current_waypoint_index = -1
        self.waypoint_reach_threshold = 5
        self.pid_heading = PIDController(Kp=1.0, Ki=0.0, Kd=0.2, setpoint=0)
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
        
        # --- Timer untuk Navigasi dan Update Peta ---
        # Timer untuk loop navigasi misi
        self.nav_timer = QTimer(self)
        self.nav_timer.timeout.connect(self.navigation_loop)
        self.nav_timer.start(200) # 5 Hz

        # === TIMER BARU: Untuk memperbarui peta secara berkala ===
        self.map_update_timer = QTimer(self)
        self.map_update_timer.timeout.connect(self.update_map_view)
        self.map_update_timer.start(2000) # Update peta setiap 2 detik
        
    # === FUNGSI BARU: Untuk mengupdate tampilan peta ===
    def update_map_view(self):
        """
        Mengambil data terbaru (posisi & waypoints) dan memerintahkan MapView
        untuk menggambar ulang peta.
        """
        # Jangan update jika belum ada data GPS
        if self.current_lat == 0.0:
            return

        waypoints = self.status_panel.get_waypoints()
        
        # Panggil fungsi update_map di MapView dengan data terbaru
        self.central_view.tab_map.update_map(
            self.current_lat, 
            self.current_lon, 
            waypoints,
            self.current_heading
        )

    # ... (sisa fungsi Anda tidak berubah) ...
    def connect_signals(self):
        self.control_panel.mission_started.connect(self.on_mission_start)
        self.control_panel.mission_paused.connect(self.on_mission_pause)
        self.central_view.tab_video.degree_changed.connect(self.control_panel.set_servo_from_yolo)
        self.central_view.tab_video.degree_changed.connect(self.status_panel.update_auto_steering_degree)
        self.control_panel.connection_status_changed.connect(self.update_header_connection_status)
        self.control_panel.mode_changed.connect(self.update_header_mode_status)
        self.status_panel.message_to_show.connect(self.show_temporary_message)
        self.control_panel.message_to_show.connect(self.show_temporary_message)
        print("Semua sinyal utama telah berhasil terhubung.")

    def on_mission_start(self):
        waypoints = self.status_panel.get_waypoints()
        if not waypoints:
            self.show_temporary_message("Cannot start mission. No waypoints added.", 4000)
            return
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.navigation_mode = "AUTO_MISSION"
        self.control_panel.is_auto_mode = True
        self.control_panel.update_ui_for_mode()
        self.show_temporary_message(f"Mission started! Heading to Waypoint 1.", 4000)

    def on_mission_pause(self):
        self.navigation_mode = "MANUAL"
        self.current_waypoint_index = -1
        self.control_panel.is_auto_mode = False
        self.control_panel.update_ui_for_mode()
        self.show_temporary_message("Mission paused. Switched to Manual mode.", 4000)

    def navigation_loop(self):
        if self.navigation_mode != "AUTO_MISSION":
            return
        if self.current_waypoint_index >= len(self.waypoints):
            self.show_temporary_message("Mission Complete!", 5000)
            self.on_mission_pause()
            return
        target_wp = self.waypoints[self.current_waypoint_index]
        target_lat, target_lon = target_wp['lat'], target_wp['lon']
        distance = haversine(self.current_lat, self.current_lon, target_lat, target_lon)
        if distance < self.waypoint_reach_threshold:
            self.show_temporary_message(f"Waypoint {self.current_waypoint_index + 1} reached!", 3000)
            self.current_waypoint_index += 1
            return
        target_bearing = calculate_bearing(self.current_lat, self.current_lon, target_lat, target_lon)
        self.pid_heading.setpoint = target_bearing
        error = target_bearing - self.current_heading
        if error > 180: error -= 360
        if error < -180: error += 360
        correction = self.pid_heading.update(self.current_heading)
        new_servo_degree = 90 - correction
        new_servo_degree = max(0, min(180, new_servo_degree))
        data_to_send = f"S1550;D{int(new_servo_degree)}\n"
        if self.serial_handler and self.serial_handler.is_connected():
            self.serial_handler.send_data(data_to_send)
            print(f"[MISSION] To WP-{self.current_waypoint_index+1} | Target: {target_bearing:.1f}°, Current: {self.current_heading:.1f}° | Servo: {int(new_servo_degree)}°")

    def handle_received_data(self, data):
        print(f"[ESP32 -> GUI]: {data}")
        if data.startswith("T:"):
            telemetry_string = data[2:]
            parts = telemetry_string.split(';')
            for part in parts:
                values = part.split(',')
                key = values[0]
                try:
                    if key == "GPS" and len(values) == 4:
                        self.current_lat = float(values[1])
                        self.current_lon = float(values[2])
                        self.status_panel.update_gps(values[1], values[2], values[3])
                    elif key == "COMP" and len(values) == 2:
                        self.current_heading = float(values[1])
                        self.status_panel.update_compass(values[1])
                except Exception as e:
                    print(f"Error parsing telemetry part '{part}': {e}")
    
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
