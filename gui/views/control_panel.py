# gui/views/control_panel.py

# Impor pustaka yang diperlukan dari PyQt5
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton,
                             QSlider, QLabel, QHBoxLayout, QTabWidget,
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal

# Impor view lain dan kontroler yang dibutuhkan
from .pid_view import PidView
from .servo_setting_view import ServoSettingView
from .system_settings_view import SystemSettingsView
from core.pid_controller import PIDController

class ControlPanel(QScrollArea):
    # --- Definisi Sinyal ---
    connection_status_changed = pyqtSignal(bool, str)
    mode_changed = pyqtSignal(bool)
    pid_data_updated = pyqtSignal(float, float)
    message_to_show = pyqtSignal(str, int)
    
    # === PERBAIKAN: Tambahkan sinyal untuk Misi ===
    mission_started = pyqtSignal()
    mission_paused = pyqtSignal()

    def __init__(self, parent=None, serial_handler=None):
        super().__init__(parent)
        
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- Variabel & Logika Inti ---
        self.serial_handler = serial_handler
        self.is_auto_mode = False
        self.current_speed_value = 1500
        self.current_servo_degree = 90
        self.servo_min_angle = 45 
        self.servo_max_angle = 135
        self.pid_steering = PIDController(Kp=0.5, Ki=0.01, Kd=0.1, setpoint=90)

        # --- Buat Widget Kontainer dan Layout ---
        container_widget = QWidget()
        main_layout = QVBoxLayout(container_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        vc_group = QGroupBox("Vehicle Control")
        vc_layout = QVBoxLayout(vc_group)
        self.mode_toggle_button = QPushButton("Switch to Auto Mode")
        self.mode_toggle_button.clicked.connect(self.toggle_mode)
        btn_emergency_stop = QPushButton("Emergency Stop")
        btn_emergency_stop.setObjectName("StopButton")
        btn_emergency_stop.clicked.connect(self.emergency_stop)
        vc_layout.addWidget(self.mode_toggle_button)
        vc_layout.addWidget(btn_emergency_stop)
        main_layout.addWidget(vc_group)
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
        main_layout.addWidget(self.manual_controls_group)
        
        # --- Grup Navigasi Otomatis ---
        self.auto_controls_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(self.auto_controls_group)
        
        # === PERBAIKAN: Hubungkan tombol misi ke fungsi baru ===
        self.start_mission_button = QPushButton("Start Mission")
        self.pause_mission_button = QPushButton("Pause Mission")
        self.return_home_button = QPushButton("Return Home")
        self.start_mission_button.clicked.connect(self.start_mission)
        self.pause_mission_button.clicked.connect(self.pause_mission)
        
        nav_layout.addWidget(self.start_mission_button)
        nav_layout.addWidget(self.pause_mission_button)
        nav_layout.addWidget(self.return_home_button)
        main_layout.addWidget(self.auto_controls_group)
        
        settings_tabs_group = QGroupBox("Settings")
        settings_tabs_layout = QVBoxLayout(settings_tabs_group)
        self.settings_tabs = QTabWidget()
        self.tab_pid_settings = PidView()
        self.tab_servo_settings = ServoSettingView()
        self.tab_connection_settings = SystemSettingsView()
        self.settings_tabs.addTab(self.tab_pid_settings, "PID")
        self.settings_tabs.addTab(self.tab_servo_settings, "Servo")
        self.settings_tabs.addTab(self.tab_connection_settings, "Connection")
        settings_tabs_layout.addWidget(self.settings_tabs)
        main_layout.addWidget(settings_tabs_group)

        # --- Koneksi Sinyal Internal ---
        self.tab_connection_settings.connection_status_changed.connect(self.relay_connection_status)
        self.pid_data_updated.connect(self.tab_pid_settings.update_graph)
        self.tab_pid_settings.pid_gains_changed.connect(self.update_pid_gains)
        self.tab_pid_settings.message_to_show.connect(self.message_to_show.emit)
        self.tab_servo_settings.servo_limits_changed.connect(self.update_servo_limits)
        self.tab_servo_settings.message_to_show.connect(self.message_to_show.emit)
        
        main_layout.addStretch()
        self.setWidget(container_widget)
        self.update_ui_for_mode()

    # === FUNGSI BARU untuk memancarkan sinyal misi ===
    def start_mission(self):
        """Memancarkan sinyal untuk memulai misi."""
        self.message_to_show.emit("Requesting to start mission...", 2000)
        self.mission_started.emit()

    def pause_mission(self):
        """Memancarkan sinyal untuk menghentikan misi."""
        self.message_to_show.emit("Mission paused!", 3000)
        self.mission_paused.emit()

    # --- Sisa Fungsi ---
    def update_pid_gains(self, kp, ki, kd):
        self.pid_steering.Kp = kp
        self.pid_steering.Ki = ki
        self.pid_steering.Kd = kd
        print(f"PID gains updated: P={kp}, I={ki}, D={kd}")

    def update_servo_limits(self, min_angle, max_angle):
        self.servo_min_angle = min_angle
        self.servo_max_angle = max_angle
        print(f"Servo limits updated: Min={min_angle}, Max={max_angle}")
        
    def set_servo_from_yolo(self, degree_from_camera):
        if self.is_auto_mode:
            correction = self.pid_steering.update(degree_from_camera)
            new_servo_degree = 90 + correction
            new_servo_degree = max(self.servo_min_angle, min(self.servo_max_angle, new_servo_degree))
            self.current_servo_degree = int(new_servo_degree)
            auto_speed_pwm = 1550
            data_to_send = f"S{auto_speed_pwm};D{self.current_servo_degree}\n"
            print(f"[AUTO-PID] Data: {data_to_send.strip()}")
            if self.serial_handler and self.serial_handler.is_connected():
                self.serial_handler.send_data(data_to_send)
            self.pid_data_updated.emit(self.pid_steering.setpoint, degree_from_camera)
            
    def relay_connection_status(self, is_connected, message):
        self.connection_status_changed.emit(is_connected, message)
    def update_speed(self, value):
        self.current_speed_value = int(1500 + (value / 100.0) * (2000 - 1500))
        self.speed_label.setText(f"Speed: {value}% | PWM: {self.current_speed_value}")
        self._send_control_data()
    def set_servo_and_send(self, degree):
        self.current_servo_degree = degree
        self._send_control_data()
    def _send_control_data(self):
        if not self.is_auto_mode:
            data_to_send = f"S{self.current_speed_value};D{self.current_servo_degree}\n"
            print(f"[MANUAL] Menyiapkan data untuk dikirim: {data_to_send.strip()}")
            if self.serial_handler and self.serial_handler.is_connected():
                self.serial_handler.send_data(data_to_send)
    def emergency_stop(self):
        data_to_send = f"S1500;D90\n"
        print(f"[EMERGENCY] Menyiapkan data untuk dikirim: {data_to_send.strip()}")
        if self.serial_handler and self.serial_handler.is_connected():
            self.serial_handler.send_data(data_to_send)
        self.message_to_show.emit("EMERGENCY STOP ACTIVATED", 5000)
    def toggle_mode(self):
        self.is_auto_mode = not self.is_auto_mode
        self.update_ui_for_mode()
        if self.is_auto_mode:
            self.pid_steering.reset()
        self.mode_changed.emit(self.is_auto_mode)
    def update_ui_for_mode(self):
        is_manual = not self.is_auto_mode
        self.mode_toggle_button.setText("Switch to Manual Mode" if self.is_auto_mode else "Switch to Auto Mode")
        self.manual_controls_group.setVisible(is_manual)
        self.auto_controls_group.setVisible(not is_manual)
