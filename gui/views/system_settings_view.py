# gui/views/system_settings_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox, QLabel
from PyQt5.QtCore import Qt # Tidak perlu import QFile, QTextStream lagi

class SystemSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        # Hapus: self.app_instance = None
        # Hapus: self.current_theme = "dark"

        settings_group = QGroupBox("System Connection")
        form_layout = QFormLayout()

        self.com_port_input = QLineEdit("COM3")
        self.nrf_channel_input = QLineEdit("108")
        self.connection_status = QLabel("Status: Disconnected")
        self.connection_status.setStyleSheet("font-weight: bold; color: #EF4444;") # Red

        form_layout.addRow("COM Port:", self.com_port_input)
        form_layout.addRow("NRF24 Channel:", self.nrf_channel_input)
        form_layout.addRow(self.connection_status)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)

        layout_in_group = QVBoxLayout()
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.connect_button)
        settings_group.setLayout(layout_in_group)

        main_layout.addWidget(settings_group)

        # --- HAPUS SELURUH BLOK INI: Theme Settings Group ---
        # theme_group = QGroupBox("Theme Settings")
        # theme_layout = QVBoxLayout()
        # self.theme_toggle_button = QPushButton("Switch to Light Theme")
        # self.theme_toggle_button.clicked.connect(self.toggle_theme)
        # theme_layout.addWidget(self.theme_toggle_button)
        # theme_group.setLayout(theme_layout)
        # main_layout.addWidget(theme_group)
        # --- AKHIR HAPUS ---

        main_layout.addStretch()

        self.is_connected = False

    # Hapus metode ini:
    # def set_application_instance(self, app):
    #     self.app_instance = app

    def toggle_connection(self):
        if not self.is_connected:
            com_port = self.com_port_input.text()
            print(f"Attempting to connect to {com_port}...")
            self.is_connected = True
            self.connection_status.setText("Status: Connected")
            self.connection_status.setStyleSheet("font-weight: bold; color: #10B981;") # Green
            self.connect_button.setText("Disconnect")
        else:
            print("Disconnecting...")
            self.is_connected = False
            self.connection_status.setText("Status: Disconnected")
            self.connection_status.setStyleSheet("font-weight: bold; color: #EF4444;") # Red
            self.connect_button.setText("Connect")

    # Hapus metode ini:
    # def toggle_theme(self):
    #     ...