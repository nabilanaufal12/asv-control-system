# gui/views/system_settings_view.py

# Impor pustaka yang diperlukan dari PyQt5
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal # <<< PENTING: Impor pyqtSignal

class SystemSettingsView(QWidget):
    # === DEFINISI SINYAL ===
    # Sinyal ini akan dipancarkan (emitted) setiap kali status koneksi berubah.
    # Ia membawa dua argumen:
    # 1. bool: True jika terhubung, False jika terputus.
    # 2. str: Pesan status yang akan ditampilkan (misalnya, "Connected", "Disconnected").
    # Sinyal ini memungkinkan widget lain (seperti DashboardWindow) untuk bereaksi terhadap perubahan koneksi.
    connection_status_changed = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        # --- Inisialisasi Variabel Status ---
        self.is_connected = False

        # --- Pengaturan Layout Utama ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Grup Pengaturan Koneksi ---
        settings_group = QGroupBox("System Connection")
        form_layout = QFormLayout()

        # Input untuk COM Port dan Channel NRF
        self.com_port_input = QLineEdit("COM3")
        self.nrf_channel_input = QLineEdit("108")

        # Label untuk menampilkan status koneksi di dalam tab ini
        # Kita ganti nama variabelnya agar lebih jelas
        self.connection_status_label = QLabel("Status: Disconnected")
        self.connection_status_label.setStyleSheet("font-weight: bold; color: #EF4444;") # Warna merah

        form_layout.addRow("COM Port:", self.com_port_input)
        form_layout.addRow("NRF24 Channel:", self.nrf_channel_input)
        form_layout.addRow(self.connection_status_label)

        # Tombol untuk memulai/menghentikan koneksi
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)

        # Menyatukan form dan tombol ke dalam grup
        layout_in_group = QVBoxLayout()
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.connect_button)
        settings_group.setLayout(layout_in_group)

        main_layout.addWidget(settings_group)
        main_layout.addStretch() # Mendorong grup ke atas

    def toggle_connection(self):
        """
        Fungsi ini dipanggil saat tombol Connect/Disconnect diklik.
        Ini akan mengubah status koneksi dan memancarkan sinyal untuk memberitahu aplikasi.
        """
        if not self.is_connected:
            # --- Logika untuk mencoba menyambung ---
            # Di sini, Anda akan menambahkan kode untuk benar-benar terhubung ke serial port.
            # Untuk sekarang, kita hanya simulasikan keberhasilan.
            com_port = self.com_port_input.text()
            print(f"Mencoba terhubung ke {com_port}...")
            
            # Asumsikan koneksi berhasil
            self.is_connected = True
            message = "Connected"
            
            # Update UI di dalam widget ini
            self.connection_status_label.setText(f"Status: {message}")
            self.connection_status_label.setStyleSheet("font-weight: bold; color: #10B981;") # Warna hijau
            self.connect_button.setText("Disconnect")
            
            # === PANCARKAN SINYAL ===
            # Kirim sinyal bahwa koneksi telah berhasil.
            self.connection_status_changed.emit(True, message)

        else:
            # --- Logika untuk memutus koneksi ---
            print("Memutus koneksi...")
            
            self.is_connected = False
            message = "Disconnected"

            # Update UI di dalam widget ini
            self.connection_status_label.setText(f"Status: {message}")
            self.connection_status_label.setStyleSheet("font-weight: bold; color: #EF4444;") # Warna merah
            self.connect_button.setText("Connect")

            # === PANCARKAN SINYAL ===
            # Kirim sinyal bahwa koneksi telah terputus.
            self.connection_status_changed.emit(False, message)