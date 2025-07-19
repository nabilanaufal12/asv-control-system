# gui/views/dashboard.py

# --- Impor Pustaka PyQt5 ---
# Tambahkan QSplitter ke daftar impor untuk layout yang fleksibel
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton, QSplitter
from PyQt5.QtCore import Qt, QFile, QTextStream, QTimer

# --- Impor Widget Kustom & Logika Inti ---
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget
from core.navigation import haversine, calculate_bearing
from core.pid_controller import PIDController
from core.serial_handler import SerialHandler

class DashboardWindow(QMainWindow):
    """
    Kelas utama untuk jendela aplikasi. Bertanggung jawab untuk merakit semua
    panel, mengelola status UI, dan menghubungkan sinyal antar widget.
    """
    def __init__(self):
        super().__init__()
        # --- Pengaturan Jendela Utama ---
        self.setWindowTitle("ASV Control System")
        self.setGeometry(100, 100, 1600, 900)

        # --- Variabel dan Objek Inti ---
        self.app = None # Untuk menyimpan instance QApplication (untuk manajemen tema)
        self.current_theme = "dark"
        # Hanya ada satu objek SerialHandler untuk seluruh aplikasi, dibuat di sini.
        self.serial_handler = SerialHandler()
        
        # Inisialisasi variabel untuk logika navigasi misi
        self.navigation_mode = "MANUAL"
        self.current_lat, self.current_lon = 0.0, 0.0
        self.current_heading = 0.0
        self.waypoints = []
        self.current_waypoint_index = -1
        self.waypoint_reach_threshold = 5 # Jarak dalam meter untuk dianggap sampai
        self.pid_heading = PIDController(Kp=1.0, Ki=0.0, Kd=0.2, setpoint=0)
        
        # Membuat status bar di bagian bawah jendela untuk pesan sementara.
        self.statusBar().showMessage("Welcome to ASV Control System!", 5000)

        # --- Membangun Struktur Layout Utama ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 1. Membuat dan menambahkan Header
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)

        # --- Merakit Panel-Panel Utama ---
        # Berikan instance serial_handler dan parent (self) ke widget yang membutuhkannya.
        self.control_panel = ControlPanel(parent=self, serial_handler=self.serial_handler)
        self.central_view = CentralWidget(parent=self)
        self.status_panel = StatusPanel(parent=self)
        self.control_panel.tab_connection_settings.set_serial_handler(self.serial_handler)
        
        # === Gunakan QSplitter untuk Layout Fleksibel ===
        # QSplitter adalah kontainer yang memungkinkan pengguna untuk mengubah ukuran widget di dalamnya.
        # Ini adalah solusi terbaik untuk mencegah panel terpotong.
        splitter = QSplitter(Qt.Horizontal)
        
        # Tambahkan ketiga panel utama ke dalam splitter
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.central_view)
        splitter.addWidget(self.status_panel)

        # Atur ukuran awal untuk setiap panel.
        splitter.setSizes([320, 960, 320])
        
        # Mencegah panel samping agar tidak bisa "disembunyikan" sepenuhnya oleh pengguna.
        splitter.setCollapsible(0, False) # Panel kiri tidak bisa disembunyikan
        splitter.setCollapsible(2, False) # Panel kanan tidak bisa disembunyikan

        # Tambahkan splitter yang sudah jadi ke layout utama aplikasi.
        self.main_layout.addWidget(splitter)

        # Menghubungkan semua sinyal antar widget.
        self.connect_signals()

        # --- Timer untuk Navigasi ---
        # Timer ini akan memanggil loop navigasi secara berkala.
        self.nav_timer = QTimer(self)
        self.nav_timer.timeout.connect(self.navigation_loop)
        self.nav_timer.start(200) # Jalankan setiap 200 ms (5 Hz)

    def connect_signals(self):
        """Fungsi terpusat untuk mengatur semua koneksi sinyal-slot."""
        # Sinyal dari tombol misi di ControlPanel dihubungkan ke slot di sini
        self.control_panel.mission_started.connect(self.on_mission_start)
        self.control_panel.mission_paused.connect(self.on_mission_pause)
        # Sinyal dari VideoView (derajat) dihubungkan ke ControlPanel dan StatusPanel
        self.central_view.tab_video.degree_changed.connect(self.control_panel.set_servo_from_yolo)
        self.central_view.tab_video.degree_changed.connect(self.status_panel.update_auto_steering_degree)
        # Sinyal dari ControlPanel (status koneksi, mode, pesan) dihubungkan ke slot di sini
        self.control_panel.connection_status_changed.connect(self.update_header_connection_status)
        self.control_panel.mode_changed.connect(self.update_header_mode_status)
        self.control_panel.message_to_show.connect(self.show_temporary_message)
        # Sinyal dari StatusPanel (pesan) dihubungkan ke slot di sini
        self.status_panel.message_to_show.connect(self.show_temporary_message)
        
        print("Semua sinyal utama telah berhasil terhubung.")

    def set_application(self, app_instance):
        """Menerima dan menyimpan instance QApplication dari main.py untuk manajemen tema."""
        self.app = app_instance

    def _create_header(self):
        """Membuat widget header di bagian atas jendela."""
        header_widget = QWidget()
        header_widget.setObjectName("Header")
        header_layout = QHBoxLayout(header_widget)
        title = QLabel("ASV Control System")
        
        # Label-label status di header dibuat sebagai atribut agar bisa diakses dari fungsi lain
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

        # Menambahkan semua elemen ke layout header
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.header_status_connection)
        header_layout.addWidget(self.header_status_gps)
        header_layout.addWidget(self.header_status_mode)
        header_layout.addWidget(self.theme_toggle_button)
        header_widget.setFixedHeight(60)
        return header_widget

    # --- Fungsi Logika dan Slot Penerima Sinyal ---

    def handle_received_data(self, data):
        """Slot untuk menangani semua data yang diterima dari ESP32."""
        print(f"[ESP32 -> GUI]: {data}")
        # Jika data adalah telemetri, urai dan perbarui variabel
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
        """Slot yang menerima sinyal untuk mengupdate status koneksi di header."""
        self.header_status_connection.setText(message)
        self.header_status_connection.setProperty("connected", is_connected)
        self.style().polish(self.header_status_connection) # Terapkan ulang style agar warna berubah
        
        # Hubungkan sinyal dari thread pembaca SETELAH koneksi berhasil dibuat.
        if is_connected and self.serial_handler.reader_thread:
            try:
                self.serial_handler.reader_thread.data_received.disconnect(self.handle_received_data)
            except TypeError:
                pass # Abaikan jika belum terhubung
            self.serial_handler.reader_thread.data_received.connect(self.handle_received_data)
        
        print(f"Header status diupdate: {message}")

    def update_header_mode_status(self, is_auto_mode):
        """Slot yang menerima sinyal untuk mengupdate status mode di header."""
        mode_text = "Auto Mode" if is_auto_mode else "Manual Mode"
        self.header_status_mode.setText(mode_text)
        self.header_status_mode.setProperty("connected", is_auto_mode)
        self.style().polish(self.header_status_mode)
        self.show_temporary_message(f"Mode switched to {mode_text.replace(' Mode', '')}", 3000)
        print(f"Header status diupdate: {mode_text}")

    def show_temporary_message(self, message, duration=3000):
        """Slot yang menerima sinyal untuk menampilkan pesan di status bar."""
        self.statusBar().showMessage(message, duration)

    def _toggle_theme(self):
        """Mengganti antara tema gelap dan terang dengan memuat file QSS."""
        if not self.app: return
        if self.current_theme == "dark":
            stylesheet_path = "gui/resources/light_theme.qss"
            self.current_theme = "light"
            self.theme_toggle_button.setText("Switch to Dark Mode")
        else:
            stylesheet_path = "gui/resources/dark_theme.qss"
            self.current_theme = "dark"
            self.theme_toggle_button.setText("Switch to Light Mode")
        try:
            with open(stylesheet_path, "r") as f:
                self.app.setStyleSheet(f.read())
        except FileNotFoundError:
            error_msg = f"Error: Gagal membuka stylesheet {stylesheet_path}"
            print(error_msg)
            self.show_temporary_message(error_msg, 5000)

    def closeEvent(self, event):
        """Dipanggil saat pengguna menutup jendela. Memastikan koneksi serial ditutup."""
        print("Closing application, disconnecting serial port...")
        self.serial_handler.disconnect()
        event.accept()

    # --- Logika Navigasi Misi ---

    def on_mission_start(self):
        """Dipanggil saat tombol 'Start Mission' ditekan."""
        waypoints = self.status_panel.get_waypoints()
        if not waypoints:
            self.show_temporary_message("Cannot start mission. No waypoints added.", 4000)
            return
            
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.navigation_mode = "AUTO_MISSION"
        # Pindahkan logika update UI ke fungsi terpisah agar lebih rapi
        self.update_mode_ui()
        self.show_temporary_message(f"Mission started! Heading to Waypoint 1.", 4000)

    def on_mission_pause(self):
        """Dipanggil saat tombol 'Pause Mission' ditekan."""
        self.navigation_mode = "MANUAL"
        self.current_waypoint_index = -1
        self.update_mode_ui()
        self.show_temporary_message("Mission paused. Switched to Manual mode.", 4000)

    def update_mode_ui(self):
        """Memperbarui UI di ControlPanel berdasarkan mode navigasi saat ini."""
        is_auto = self.navigation_mode != "MANUAL"
        self.control_panel.is_auto_mode = is_auto
        self.control_panel.update_ui_for_mode()

    def navigation_loop(self):
        """Loop utama yang berjalan setiap 200ms untuk navigasi otonom."""
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

