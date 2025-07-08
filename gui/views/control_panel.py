# gui/views/control_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton,
                             QSlider, QLabel, QHBoxLayout, QLineEdit, QTabWidget,
                             QScrollArea) # <<< IMPORT QScrollArea
from PyQt5.QtCore import Qt
from .pid_view import PidView
from .servo_setting_view import ServoSettingView
from .system_settings_view import SystemSettingsView

class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.is_auto_mode = False

        # --- Main Layout for the ControlPanel (this is the container for the scroll area) ---
        outer_layout = QVBoxLayout(self) # Layout terluar untuk ControlPanel
        outer_layout.setContentsMargins(0, 0, 0, 0) # Hapus margin agar scroll area bisa penuh

        # --- QScrollArea ---
        self.scroll_area = QScrollArea(self) # Buat QScrollArea
        self.scroll_area.setWidgetResizable(True) # Izinkan widget di dalamnya untuk diubah ukurannya
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Matikan scrollbar horizontal
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # Tampilkan scrollbar vertikal jika perlu

        # --- Widget Konten untuk QScrollArea ---
        # Ini adalah widget tempat semua konten kontrol panel akan diletakkan
        self.scroll_content_widget = QWidget()
        self.main_layout = QVBoxLayout(self.scroll_content_widget) # <<<< SEMUA KONTEN PANEL MASUK SINI
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Margin konten di dalam scroll area
        self.main_layout.setSpacing(15) # Spasi antar grup utama

        # --- Masukkan semua QGroupBoxes ke self.main_layout ini ---

        # Vehicle Control Group
        vc_group = QGroupBox("Vehicle Control")
        vc_layout = QVBoxLayout()
        vc_layout.setSpacing(10)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_toggle_button = QPushButton("Switch to Auto Mode")
        self.mode_toggle_button.clicked.connect(self.toggle_mode)
        mode_layout.addWidget(self.mode_toggle_button)
        vc_layout.addLayout(mode_layout)

        btn_emergency_stop = QPushButton("Emergency Stop")
        btn_emergency_stop.setObjectName("StopButton")
        vc_layout.addWidget(btn_emergency_stop)

        vc_group.setLayout(vc_layout)
        self.main_layout.addWidget(vc_group) # Tambahkan ke self.main_layout

        # Manual Control Widgets
        self.manual_controls_group = QGroupBox("Manual Control")
        manual_layout = QVBoxLayout()
        manual_layout.setSpacing(10)

        dir_layout = QHBoxLayout()
        btn_left = QPushButton("Left")
        btn_forward = QPushButton("Forward")
        btn_right = QPushButton("Right")
        dir_layout.addWidget(btn_left)
        dir_layout.addWidget(btn_forward)
        dir_layout.addWidget(btn_right)
        manual_layout.addLayout(dir_layout)

        self.speed_label = QLabel("Speed: 50%")
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(0, 100)
        speed_slider.setValue(50)
        speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"Speed: {v}%"))
        manual_layout.addWidget(self.speed_label)
        manual_layout.addWidget(speed_slider)
        self.manual_controls_group.setLayout(manual_layout)
        self.main_layout.addWidget(self.manual_controls_group) # Tambahkan ke self.main_layout

        # Auto Navigation Group
        self.auto_controls_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(10)
        
        btn_start_mission = QPushButton("Start Mission")
        btn_pause_mission = QPushButton("Pause Mission")
        btn_return_home = QPushButton("Return Home")
        nav_layout.addWidget(btn_start_mission)
        nav_layout.addWidget(btn_pause_mission)
        nav_layout.addWidget(btn_return_home)
        self.auto_controls_group.setLayout(nav_layout)
        self.main_layout.addWidget(self.auto_controls_group) # Tambahkan ke self.main_layout

        # GroupBox for Settings Tabs
        settings_tabs_group = QGroupBox("Settings")
        settings_tabs_layout = QVBoxLayout(settings_tabs_group)
        
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setContentsMargins(5,5,5,5)

        self.tab_pid_settings = PidView()
        self.tab_servo_settings = ServoSettingView()
        self.tab_connection_settings = SystemSettingsView()

        self.settings_tabs.addTab(self.tab_pid_settings, "PID")
        self.settings_tabs.addTab(self.tab_servo_settings, "Servo")
        self.settings_tabs.addTab(self.tab_connection_settings, "Connection")

        settings_tabs_layout.addWidget(self.settings_tabs)
        self.main_layout.addWidget(settings_tabs_group) # Tambahkan ke self.main_layout

        self.main_layout.addStretch() # Pushes everything to the top of the scroll content

        # <<< PENTING: Set widget konten ke QScrollArea >>>
        self.scroll_area.setWidget(self.scroll_content_widget)

        # <<< PENTING: Tambahkan QScrollArea ke layout terluar ControlPanel >>>
        outer_layout.addWidget(self.scroll_area)


        # Set initial visibility based on the default mode
        self.update_ui_for_mode()

    def toggle_mode(self):
        self.is_auto_mode = not self.is_auto_mode
        self.update_ui_for_mode()

    def update_ui_for_mode(self):
        if self.is_auto_mode:
            self.mode_toggle_button.setText("Switch to Manual Mode")
            self.manual_controls_group.setVisible(False)
            self.auto_controls_group.setVisible(True)
        else:
            self.mode_toggle_button.setText("Switch to Auto Mode")
            self.manual_controls_group.setVisible(True)
            self.auto_controls_group.setVisible(False)