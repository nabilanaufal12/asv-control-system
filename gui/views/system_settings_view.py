# gui/views/system_settings_view.py

# Ganti QLineEdit dengan QComboBox untuk dropdown, dan tambahkan QHBoxLayout
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                             QPushButton, QGroupBox, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class SystemSettingsView(QWidget):
    """
    Widget tab untuk pengaturan koneksi sistem.
    Mengelola pemilihan COM port, koneksi, dan pemutusan hubungan dengan hardware.
    """
    # Sinyal yang akan dipancarkan saat status koneksi berubah.
    # Akan ditangkap oleh ControlPanel dan diteruskan ke DashboardWindow.
    connection_status_changed = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Inisialisasi handler serial, akan diisi oleh DashboardWindow nanti.
        self.serial_handler = None

        # --- Pengaturan Layout Utama ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Grup Pengaturan Koneksi ---
        settings_group = QGroupBox("System Connection")
        form_layout = QFormLayout()

        # === PERUBAHAN: Gunakan QComboBox (Dropdown) untuk COM Port ===
        self.com_port_combo = QComboBox()
        self.refresh_ports_button = QPushButton("Refresh")
        self.refresh_ports_button.clicked.connect(self.populate_ports)
        
        # Buat layout horizontal untuk menempatkan dropdown dan tombol refresh berdampingan.
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.com_port_combo)
        port_layout.addWidget(self.refresh_ports_button)

        # Label untuk menampilkan status koneksi di dalam tab ini.
        self.connection_status_label = QLabel("Status: Disconnected")
        self.connection_status_label.setStyleSheet("font-weight: bold; color: #EF4444;") # Merah

        # Menambahkan baris COM port (yang sekarang berisi layout horizontal) ke form.
        form_layout.addRow("COM Port:", port_layout)
        form_layout.addRow(self.connection_status_label)

        # Tombol untuk memulai/menghentikan koneksi.
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)

        # Menyatukan form dan tombol ke dalam grup.
        layout_in_group = QVBoxLayout()
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.connect_button)
        settings_group.setLayout(layout_in_group)

        main_layout.addWidget(settings_group)
        main_layout.addStretch()

    def set_serial_handler(self, handler):
        """
        Menerima instance SerialHandler dari DashboardWindow.
        Ini adalah 'jembatan' yang menghubungkan UI ini dengan logika serial.
        """
        self.serial_handler = handler
        # Langsung isi daftar port saat handler pertama kali diterima.
        self.populate_ports()

    def populate_ports(self):
        """
        Membersihkan dan mengisi ulang dropdown dengan daftar COM port yang tersedia.
        Dipanggil saat startup dan saat tombol 'Refresh' ditekan.
        """
        if not self.serial_handler:
            return
        self.com_port_combo.clear() # Kosongkan daftar lama
        ports = self.serial_handler.list_available_ports()
        if ports:
            self.com_port_combo.addItems(ports)
            self.connect_button.setEnabled(True) # Aktifkan tombol connect jika ada port
        else:
            self.com_port_combo.addItem("Tidak ada port ditemukan")
            self.connect_button.setEnabled(False) # Nonaktifkan jika tidak ada port

    def toggle_connection(self):
        """
        Menghubungkan atau memutus koneksi menggunakan SerialHandler.
        Fungsi ini dipanggil saat tombol 'Connect'/'Disconnect' diklik.
        """
        if not self.serial_handler:
            print("Error: Serial Handler belum diatur!")
            return

        if not self.serial_handler.is_connected():
            # --- Logika untuk Menyambung ---
            selected_port = self.com_port_combo.currentText()
            if "Tidak ada port" in selected_port:
                return
            
            # Coba hubungkan menggunakan handler
            success = self.serial_handler.connect(selected_port)
            
            if success:
                message = "Connected"
                # Update UI di tab ini
                self.connection_status_label.setText(f"Status: {message}")
                self.connection_status_label.setStyleSheet("font-weight: bold; color: #10B981;") # Hijau
                self.connect_button.setText("Disconnect")
                self.com_port_combo.setEnabled(False) # Nonaktifkan dropdown saat terhubung
                self.refresh_ports_button.setEnabled(False)
                # Pancarkan sinyal sukses ke seluruh aplikasi
                self.connection_status_changed.emit(True, message)
            else:
                message = "Failed to connect"
                self.connection_status_label.setText(f"Status: {message}")
                # Pancarkan sinyal gagal
                self.connection_status_changed.emit(False, message)
        else:
            # --- Logika untuk Memutus Koneksi ---
            self.serial_handler.disconnect()
            message = "Disconnected"
            # Update UI di tab ini
            self.connection_status_label.setText(f"Status: {message}")
            self.connection_status_label.setStyleSheet("font-weight: bold; color: #EF4444;") # Merah
            self.connect_button.setText("Connect")
            self.com_port_combo.setEnabled(True) # Aktifkan kembali dropdown
            self.refresh_ports_button.setEnabled(True)
            # Pancarkan sinyal bahwa koneksi telah terputus
            self.connection_status_changed.emit(False, message)
