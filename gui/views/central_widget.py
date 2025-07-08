# gui/views/central_widget.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from .map_view import MapView
from .video_view import VideoView
# Hapus import untuk PidView, ServoSettingView, SystemSettingsView dari sini
# from .pid_view import PidView
# from .servo_setting_view import ServoSettingView
# from .system_settings_view import SystemSettingsView


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)

        # Create Tab Widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Create and add tabs
        self.tab_map = MapView()
        # Hapus instansiasi untuk PidView, ServoSettingView, SystemSettingsView dari sini
        # self.tab_pid = PidView()
        # self.tab_servo = ServoSettingView()
        # self.tab_system = SystemSettingsView()

        # A dummy video stream tab to match the image
        self.tab_video = VideoView()

        self.tabs.addTab(self.tab_video, "Video Stream")
        self.tabs.addTab(self.tab_map, "Map View")
        # Hapus penambahan tab untuk PID Settings, Servo Settings, Connection dari sini
        # self.tabs.addTab(self.tab_pid, "PID Settings")
        # self.tabs.addTab(self.tab_servo, "Servo Settings")
        # self.tabs.addTab(self.tab_system, "Connection")