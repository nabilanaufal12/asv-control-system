# gui/views/central_widget.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

# Impor view lain yang akan menjadi isi dari tab
from .map_view import MapView
from .video_view import VideoView

class CentralWidget(QWidget):
    """
    Widget sentral yang berisi tampilan utama aplikasi, seperti video dan peta,
    yang diorganisir dalam bentuk tab.
    """
    
    # === PERBAIKAN UTAMA ===
    # 1. Tambahkan 'parent=None' pada argumen __init__.
    #    Ini memungkinkan widget untuk menerima referensi ke induknya (yaitu, DashboardWindow).
    def __init__(self, parent=None):
        # 2. Teruskan 'parent' ke konstruktor superclass (QWidget).
        #    Ini adalah praktik standar di PyQt untuk memastikan widget terintegrasi
        #    dengan benar ke dalam hierarki aplikasi.
        super().__init__(parent)

        # Layout utama untuk widget ini
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 10, 0, 0) # Beri sedikit margin di atas

        # --- Buat dan Konfigurasi Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setObjectName("CentralTabs") # Beri nama objek untuk styling QSS

        # --- Buat Instance dari Setiap View ---
        # Membuat objek dari kelas VideoView dan MapView
        self.tab_video = VideoView()
        self.tab_map = MapView()

        # --- Tambahkan View ke dalam Tabs ---
        # Menambahkan instance view yang sudah dibuat sebagai tab baru
        self.tabs.addTab(self.tab_video, "Video Stream")
        self.tabs.addTab(self.tab_map, "Map View")

        # Tambahkan QTabWidget yang sudah diisi ke layout utama
        self.main_layout.addWidget(self.tabs)