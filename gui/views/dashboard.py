# gui/views/dashboard.py

# --- Impor Pustaka PyQt5 ---
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QFile, QTextStream

# --- Impor Widget Kustom ---
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .central_widget import CentralWidget

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
        self.app = None # Untuk menyimpan instance QApplication (manajemen tema)
        self.current_theme = "dark"

        # === BUAT STATUS BAR DI BAGIAN BAWAH JENDELA ===
        # Status bar ini akan digunakan untuk menampilkan pesan sementara.
        self.statusBar().showMessage("Welcome to ASV Control System!", 5000) # Pesan hilang setelah 5 detik

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
        # PENTING: Berikan 'self' (instance DashboardWindow) sebagai 'parent'.
        # Ini memungkinkan panel anak untuk memanggil fungsi di DashboardWindow,
        # seperti show_temporary_message().
        self.control_panel = ControlPanel(parent=self)
        self.central_view = CentralWidget(parent=self)
        self.status_panel = StatusPanel(parent=self)
        
        self.content_layout.addWidget(self.control_panel, 1) # Faktor stretch 1
        self.content_layout.addWidget(self.central_view, 3)  # Faktor stretch 3 (lebih lebar)
        self.content_layout.addWidget(self.status_panel, 1)  # Faktor stretch 1

        # Menghubungkan semua "kabel" komunikasi antar widget.
        self.connect_signals()

    def connect_signals(self):
        """Fungsi terpusat untuk mengatur semua koneksi sinyal-slot."""
        # 1. Sinyal dari VideoView (derajat YOLO) ke ControlPanel (untuk mengirim data kontrol)
        self.central_view.tab_video.degree_changed.connect(self.control_panel.set_servo_from_yolo)
        
        # 2. Sinyal dari VideoView (derajat YOLO) ke StatusPanel (untuk ditampilkan di UI)
        self.central_view.tab_video.degree_changed.connect(self.status_panel.update_auto_steering_degree)
        
        # 3. Sinyal dari ControlPanel (yang meneruskan status koneksi) ke Dashboard (untuk update header)
        self.control_panel.connection_status_changed.connect(self.update_header_connection_status)
        
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

        # --- Label Status di Header (dibuat sebagai atribut instance agar bisa diubah) ---
        self.header_status_connection = QLabel("Disconnected")
        self.header_status_connection.setObjectName("StatusLabel")
        self.header_status_connection.setProperty("connected", False) # Properti untuk styling QSS

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

    # === SLOT UNTUK MENERIMA SINYAL ===

    def update_header_connection_status(self, is_connected, message):
        """Slot yang menerima sinyal dari ControlPanel untuk mengupdate header."""
        self.header_status_connection.setText(message)
        self.header_status_connection.setProperty("connected", is_connected)
        # 'polish' penting untuk memberitahu PyQt agar menerapkan ulang stylesheet
        # berdasarkan properti 'connected' yang baru, sehingga warnanya berubah.
        self.style().polish(self.header_status_connection)
        print(f"Header status diupdate: {message}")

    # === FUNGSI PUBLIK & UTILITAS ===

    def show_temporary_message(self, message, duration=3000):
        """
        Fungsi publik yang bisa dipanggil oleh widget anak (seperti ControlPanel)
        untuk menampilkan pesan di status bar.
        """
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

