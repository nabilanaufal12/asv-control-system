# gui/views/status_panel.py

# --- Impor Pustaka PyQt5 ---
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QHBoxLayout, QPushButton,
                             QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator

class StatusPanel(QWidget):
    """
    Panel di sisi kanan aplikasi yang menampilkan status sistem secara real-time
    dan menyediakan fungsionalitas untuk manajemen waypoint.
    """
    # === DEFINISI SINYAL ===
    # Sinyal ini digunakan untuk mengirim pesan ke jendela utama (DashboardWindow)
    # agar ditampilkan di status bar bawah.
    # Membawa dua argumen: (str: pesan_yang_akan_ditampilkan, int: durasi_dalam_milidetik)
    message_to_show = pyqtSignal(str, int)

    def __init__(self, parent=None):
        # Menerima 'parent' agar widget ini bisa terintegrasi dengan benar
        super().__init__(parent)
        
        # --- Layout Utama ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # --- Grup Waypoints ---
        wp_group = QGroupBox("Waypoints")
        wp_layout = QVBoxLayout(wp_group)
        
        # Form untuk memasukkan koordinat waypoint baru
        wp_form_layout = QFormLayout()
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        
        # Validator untuk memastikan input adalah angka desimal yang valid
        lat_validator = QDoubleValidator(-90.0, 90.0, 7, self) # Rentang Latitude: -90 hingga +90
        lon_validator = QDoubleValidator(-180.0, 180.0, 7, self) # Rentang Longitude: -180 hingga +180
        self.lat_input.setValidator(lat_validator)
        self.lon_input.setValidator(lon_validator)
        self.lat_input.setPlaceholderText("contoh: -6.2100") # Teks bantuan untuk pengguna
        self.lon_input.setPlaceholderText("contoh: 106.8400")
        
        wp_form_layout.addRow("Latitude:", self.lat_input)
        wp_form_layout.addRow("Longitude:", self.lon_input)
        wp_layout.addLayout(wp_form_layout)
        
        # Tombol-tombol aksi untuk waypoint
        wp_buttons_layout = QHBoxLayout()
        self.add_wp_button = QPushButton("Add")
        self.delete_wp_button = QPushButton("Delete")
        self.send_all_wp_button = QPushButton("Send All")
        
        # Menghubungkan tombol ke fungsi logikanya masing-masing
        self.add_wp_button.clicked.connect(self.add_waypoint)
        self.delete_wp_button.clicked.connect(self.delete_selected_waypoint)
        self.send_all_wp_button.clicked.connect(self.send_all_waypoints)
        
        wp_buttons_layout.addWidget(self.add_wp_button)
        wp_buttons_layout.addWidget(self.delete_wp_button)
        wp_buttons_layout.addWidget(self.send_all_wp_button)
        wp_layout.addLayout(wp_buttons_layout)
        
        # Daftar untuk menampilkan waypoint yang telah ditambahkan
        self.wp_list = QListWidget()
        self.wp_list.itemSelectionChanged.connect(self._update_delete_button_state) # Update tombol delete saat item dipilih
        wp_layout.addWidget(self.wp_list)
        
        wp_group.setLayout(wp_layout)
        self.main_layout.addWidget(wp_group)

        # --- Grup Status Sistem ---
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        
        # Fungsi bantuan untuk membuat baris status (Label Kiri, Nilai Kanan)
        def create_status_label_pair(title, initial_value):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(title))
            value_label = QLabel(initial_value)
            value_label.setAlignment(Qt.AlignRight) # Ratakan kanan untuk nilai
            value_label.setObjectName("ValueLabel") # Untuk styling QSS
            h_layout.addWidget(value_label)
            return h_layout, value_label
            
        # Membuat dan menambahkan setiap baris status sensor
        sensor_status_items = [
            create_status_label_pair("GPS:", "N/A"),
            create_status_label_pair("Battery:", "N/A"),
            create_status_label_pair("Compass:", "N/A"),
            create_status_label_pair("Speed:", "N/A"),
        ]
        for layout, _ in sensor_status_items:
            status_layout.addLayout(layout)
            
        # Baris khusus untuk menampilkan derajat dari deteksi YOLO
        steering_layout, self.auto_steering_label = create_status_label_pair("Auto-Steering:", "N/A")
        status_layout.addLayout(steering_layout)
        
        status_layout.addSpacing(10) # Beri sedikit spasi
        status_layout.addWidget(QLabel("--- Communication ---"))
        
        # Membuat dan menambahkan baris status komunikasi
        comm_status_items = [
            create_status_label_pair("Radio Link:", "N/A"),
            create_status_label_pair("Telemetry:", "N/A"),
        ]
        for layout, _ in comm_status_items:
            status_layout.addLayout(layout)
            
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)
        self.main_layout.addStretch() # Mendorong semua grup ke atas
        self._update_delete_button_state() # Atur status awal tombol delete

    # === FUNGSI LOGIKA UNTUK WAYPOINT ===

    def add_waypoint(self):
        """Dipanggil saat tombol 'Add' ditekan. Menambahkan waypoint ke daftar."""
        lat = self.lat_input.text().strip().replace(',', '.') # Ambil teks & ganti koma dengan titik
        lon = self.lon_input.text().strip().replace(',', '.')
        if lat and lon:
            item_text = f"WP {self.wp_list.count() + 1}: Lat {lat}, Lon {lon}"
            self.wp_list.addItem(QListWidgetItem(item_text))
            self.lat_input.clear() # Kosongkan input field
            self.lon_input.clear()
            # Pancarkan sinyal untuk menampilkan pesan sukses di status bar
            self.message_to_show.emit(f"Waypoint {self.wp_list.count()} added!", 3000)
        else:
            # Pancarkan sinyal untuk menampilkan pesan error
            self.message_to_show.emit("Latitude and Longitude cannot be empty.", 3000)

    def delete_selected_waypoint(self):
        """Dipanggil saat tombol 'Delete' ditekan. Menghapus item yang dipilih."""
        selected_item = self.wp_list.currentItem()
        if selected_item:
            row = self.wp_list.row(selected_item)
            self.wp_list.takeItem(row) # Hapus item dari daftar
            self._relabel_waypoints() # Perbarui nomor urut waypoint
            self.message_to_show.emit("Waypoint deleted.", 3000)

    def send_all_waypoints(self):
        """(Simulasi) Dipanggil saat tombol 'Send All' ditekan."""
        count = self.wp_list.count()
        if count == 0:
            self.message_to_show.emit("No waypoints to send.", 3000)
            return
        print(f"Sending {count} waypoints to ASV...")
        # Di sini akan ada logika untuk mengirim data waypoint via serial
        self.message_to_show.emit(f"Sent {count} waypoints to ASV.", 4000)

    def _relabel_waypoints(self):
        """Memperbarui nomor urut 'WP X' setelah ada yang dihapus agar urutannya benar."""
        for i in range(self.wp_list.count()):
            item = self.wp_list.item(i)
            text_parts = item.text().split(': ', 1)
            if len(text_parts) > 1:
                item.setText(f"WP {i + 1}: {text_parts[1]}")

    def _update_delete_button_state(self):
        """Mengaktifkan tombol 'Delete' hanya jika ada item yang dipilih."""
        self.delete_wp_button.setEnabled(len(self.wp_list.selectedItems()) > 0)

    # === SLOT PUBLIK UNTUK MENERIMA SINYAL ===
    
    def update_auto_steering_degree(self, degree):
        """Slot yang menerima sinyal dari VideoView untuk mengupdate label derajat."""
        self.auto_steering_label.setText(f"{degree}°")

