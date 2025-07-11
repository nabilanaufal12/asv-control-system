# gui/views/control_panel.py

# Impor pustaka yang diperlukan dari PyQt5
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton,
                             QSlider, QLabel, QHBoxLayout, QTabWidget,
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal

# Impor view lain yang akan digunakan sebagai tab
from .pid_view import PidView
from .servo_setting_view import ServoSettingView
from .system_settings_view import SystemSettingsView

class ControlPanel(QWidget):
    """
    Panel kontrol utama di sisi kiri aplikasi.
    Mengelola input manual, mode operasi, dan pengaturan sistem.
    """
    # === DEFINISI SINYAL ===
    # Sinyal ini digunakan untuk berkomunikasi dengan widget lain (terutama DashboardWindow).
    
    # Sinyal untuk meneruskan status koneksi dari tab 'Connection' ke atas.
    # Membawa (bool: is_connected, str: message)
    connection_status_changed = pyqtSignal(bool, str)
    
    # Sinyal untuk memberitahu bahwa mode operasi telah berubah.
    # Membawa (bool: is_auto_mode) -> True untuk Auto, False untuk Manual.
    mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        # Menerima 'parent' agar bisa memanggil fungsi di DashboardWindow jika diperlukan.
        super().__init__(parent)
        
        # --- Variabel Status Internal ---
        self.is_auto_mode = False  # Menyimpan status mode saat ini (default: Manual)
        self.current_speed_value = 1500 # Menyimpan nilai PWM motor terakhir
        self.current_servo_degree = 90  # Menyimpan nilai derajat servo terakhir

        # --- Pengaturan Layout Utama & Scroll Area ---
        # Menggunakan QScrollArea agar panel bisa di-scroll jika kontennya terlalu panjang.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget konten yang akan berisi semua elemen UI dan ditempatkan di dalam scroll area.
        self.scroll_content_widget = QWidget()
        self.main_layout = QVBoxLayout(self.scroll_content_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # --- Grup Kontrol Kendaraan (Mode & Emergency Stop) ---
        vc_group = QGroupBox("Vehicle Control")
        vc_layout = QVBoxLayout(vc_group)
        self.mode_toggle_button = QPushButton("Switch to Auto Mode")
        self.mode_toggle_button.clicked.connect(self.toggle_mode)
        btn_emergency_stop = QPushButton("Emergency Stop")
        btn_emergency_stop.setObjectName("StopButton") # Untuk styling QSS
        btn_emergency_stop.clicked.connect(self.emergency_stop)
        vc_layout.addWidget(self.mode_toggle_button)
        vc_layout.addWidget(btn_emergency_stop)
        self.main_layout.addWidget(vc_group)

        # --- Grup Kontrol Manual (Arah & Kecepatan) ---
        self.manual_controls_group = QGroupBox("Manual Control")
        manual_layout = QVBoxLayout(self.manual_controls_group)
        dir_layout = QHBoxLayout()
        btn_left = QPushButton("Left")
        btn_forward = QPushButton("Forward")
        btn_right = QPushButton("Right")
        btn_left.clicked.connect(lambda: self.set_servo_and_send(45))
        btn_forward.clicked.connect(lambda: self.set_servo_and_send(90))
        btn_right.clicked.connect(lambda: self.set_servo_and_send(135))
        dir_layout.addWidget(btn_left)
        dir_layout.addWidget(btn_forward)
        dir_layout.addWidget(btn_right)
        manual_layout.addLayout(dir_layout)
        self.speed_label = QLabel(f"Speed: 0% | PWM: {self.current_speed_value}")
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(0, 100)
        speed_slider.setValue(0)
        speed_slider.valueChanged.connect(self.update_speed)
        manual_layout.addWidget(self.speed_label)
        manual_layout.addWidget(speed_slider)
        self.main_layout.addWidget(self.manual_controls_group)

        # --- Grup Navigasi Otomatis (Mission) ---
        self.auto_controls_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(self.auto_controls_group)
        nav_layout.addWidget(QPushButton("Start Mission"))
        nav_layout.addWidget(QPushButton("Pause Mission"))
        nav_layout.addWidget(QPushButton("Return Home"))
        self.main_layout.addWidget(self.auto_controls_group)

        # --- Grup Pengaturan (dalam bentuk Tab) ---
        settings_tabs_group = QGroupBox("Settings")
        settings_tabs_layout = QVBoxLayout(settings_tabs_group)
        self.settings_tabs = QTabWidget()
        self.tab_connection_settings = SystemSettingsView() # Buat instance tab koneksi
        self.settings_tabs.addTab(PidView(), "PID")
        self.settings_tabs.addTab(ServoSettingView(), "Servo")
        self.settings_tabs.addTab(self.tab_connection_settings, "Connection")
        settings_tabs_layout.addWidget(self.settings_tabs)
        self.main_layout.addWidget(settings_tabs_group)

        # Hubungkan sinyal dari tab koneksi ke fungsi relay di panel ini.
        self.tab_connection_settings.connection_status_changed.connect(self.relay_connection_status)
        
        # --- Finalisasi Layout ---
        self.main_layout.addStretch() # Mendorong semua konten ke atas
        self.scroll_area.setWidget(self.scroll_content_widget) # Masukkan konten ke scroll area
        outer_layout.addWidget(self.scroll_area) # Masukkan scroll area ke layout utama
        self.update_ui_for_mode() # Atur visibilitas awal

    # === FUNGSI SLOT & LOGIKA ===

    def relay_connection_status(self, is_connected, message):
        """Slot yang menerima sinyal dari anak (SystemSettingsView) dan meneruskannya ke atas."""
        self.connection_status_changed.emit(is_connected, message)

    def update_speed(self, value):
        """Dipanggil saat slider kecepatan digerakkan. Mengubah % ke PWM."""
        self.current_speed_value = int(1500 + (value / 100.0) * (2000 - 1500))
        self.speed_label.setText(f"Speed: {value}% | PWM: {self.current_speed_value}")
        self._send_control_data()

    def set_servo_and_send(self, degree):
        """Dipanggil saat tombol arah ditekan untuk mengatur sudut servo."""
        self.current_servo_degree = degree
        self._send_control_data()

    def _send_control_data(self):
        """(Simulasi) Mengirim data kontrol kecepatan dan servo jika dalam mode manual."""
        if not self.is_auto_mode:
            data_to_send = f"S{self.current_speed_value};D{self.current_servo_degree}\n"
            print(f"[SERIAL SEND] Mengirim data: {data_to_send.strip()}")

    def set_servo_from_yolo(self, degree):
        """Slot yang menerima sinyal derajat dari VideoView saat mode auto aktif."""
        if self.is_auto_mode:
            self.current_servo_degree = degree
            auto_speed_pwm = 1550 # Kecepatan konstan saat mode auto (contoh)
            data_to_send = f"S{auto_speed_pwm};D{self.current_servo_degree}\n"
            print(f"[AUTO-YOLO] Mengirim data: {data_to_send.strip()}")

    def emergency_stop(self):
        """Mengirim perintah berhenti darurat ke ASV."""
        data_to_send = f"S1500;D90\n" # Perintah PWM netral dan servo tengah
        print(f"[EMERGENCY STOP] Mengirim perintah berhenti: {data_to_send.strip()}")
        # Memberi notifikasi di status bar melalui parent (DashboardWindow)
        if self.parent():
            self.parent().show_temporary_message("EMERGENCY STOP ACTIVATED", 5000)

    def toggle_mode(self):
        """Mengganti antara mode Manual dan Auto, lalu memancarkan sinyal."""
        self.is_auto_mode = not self.is_auto_mode
        self.update_ui_for_mode()
        
        # Pancarkan sinyal untuk memberitahu seluruh aplikasi tentang perubahan mode.
        self.mode_changed.emit(self.is_auto_mode)

    def update_ui_for_mode(self):
        """Menyembunyikan/menampilkan grup kontrol berdasarkan mode yang aktif."""
        is_manual = not self.is_auto_mode
        self.mode_toggle_button.setText("Switch to Manual Mode" if self.is_auto_mode else "Switch to Auto Mode")
        self.manual_controls_group.setVisible(is_manual)
        self.auto_controls_group.setVisible(not is_manual)
