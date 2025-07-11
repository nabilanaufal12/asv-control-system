# gui/views/dashboard.py

# --- Impor Pustaka PyQt5 ---
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QFile, QTextStream

# --- Impor Widget Kustom ---
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget

# === IMPOR BARU ===
# Impor kelas SerialHandler yang telah kita buat untuk mengelola komunikasi serial.
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

        # --- Variabel Status Aplikasi ---
        self.app = None # Untuk menyimpan instance QApplication (untuk manajemen tema)
        self.current_theme = "dark"

        # === BUAT INSTANCE SERIAL HANDLER ===
        # Hanya ada satu objek SerialHandler untuk seluruh aplikasi, dibuat di sini.
        self.serial_handler = SerialHandler()

        # === BUAT STATUS BAR DI BAGIAN BAWAH JENDELA ===
        # Status bar ini akan digunakan untuk menampilkan pesan sementara.
        self.statusBar().showMessage("Welcome to ASV Control System!", 5000)

        # --- Membangun Struktur Layout Utama ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 1. Membuat dan menambahkan Header
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)

        # 2. Membuat layout konten utama (horizontal)
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # --- Merakit Panel-Panel Utama ---
        # Berikan instance serial_handler dan parent (self) ke widget yang membutuhkannya.
        self.control_panel = ControlPanel(parent=self, serial_handler=self.serial_handler)
        self.central_view = CentralWidget(parent=self)
        self.status_panel = StatusPanel(parent=self)
        
        # Berikan instance serial_handler ke tab koneksi yang berada di dalam control_panel.
        self.control_panel.tab_connection_settings.set_serial_handler(self.serial_handler)
        
        # Menambahkan panel-panel ke layout konten
        self.content_layout.addWidget(self.control_panel, 1) # Faktor stretch 1
        self.content_layout.addWidget(self.central_view, 3)  # Faktor stretch 3 (lebih lebar)
        self.content_layout.addWidget(self.status_panel, 1)  # Faktor stretch 1

        # Menghubungkan semua "kabel" komunikasi antar widget.
        self.connect_signals()

    def connect_signals(self):
        """Fungsi terpusat untuk mengatur semua koneksi sinyal-slot."""
        # Sinyal dari VideoView (derajat) dihubungkan ke ControlPanel (untuk mengirim data)
        self.central_view.tab_video.degree_changed.connect(self.control_panel.set_servo_from_yolo)
        # Sinyal dari VideoView (derajat) juga dihubungkan ke StatusPanel (untuk ditampilkan)
        self.central_view.tab_video.degree_changed.connect(self.status_panel.update_auto_steering_degree)
        # Sinyal dari ControlPanel (status koneksi) dihubungkan ke fungsi update header
        self.control_panel.connection_status_changed.connect(self.update_header_connection_status)
        # Sinyal dari ControlPanel (perubahan mode) dihubungkan ke fungsi update header
        self.control_panel.mode_changed.connect(self.update_header_mode_status)
        # Sinyal dari StatusPanel (pesan) dihubungkan ke fungsi di status bar
        self.status_panel.message_to_show.connect(self.show_temporary_message)
        
        # Hubungkan sinyal data yang diterima dari thread pembaca ke fungsi penangan
        if self.serial_handler.reader_thread:
            self.serial_handler.reader_thread.data_received.connect(self.handle_received_data)

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

    def handle_received_data(self, data):
        """Slot untuk menangani data yang diterima dari ESP32."""
        print(f"[ESP32 -> GUI]: {data}")
        # Di masa depan, Anda bisa mengurai data ini untuk mengupdate status GPS, baterai, dll.
        # Contoh:
        # if data.startswith("GPS:"):
        #     self.status_panel.gps_value_label.setText(data.split(':')[1].strip())

    def update_header_connection_status(self, is_connected, message):
        """Slot yang menerima sinyal untuk mengupdate status koneksi di header."""
        self.header_status_connection.setText(message)
        self.header_status_connection.setProperty("connected", is_connected)
        self.style().polish(self.header_status_connection) # Terapkan ulang style agar warna berubah
        
        # Hubungkan atau putuskan sinyal pembaca saat koneksi berubah
        if is_connected and self.serial_handler.reader_thread:
            self.serial_handler.reader_thread.data_received.connect(self.handle_received_data)
        else:
            # Cari cara untuk memutus koneksi sinyal jika diperlukan,
            # tapi biasanya thread yang berhenti sudah cukup.
            pass
        
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
        """Dipanggil saat pengguna menutup jendela. Memastikan koneksi serial ditutup."""
        print("Closing application, disconnecting serial port...")
        self.serial_handler.disconnect()
        event.accept() # Izinkan jendela untuk ditutup
