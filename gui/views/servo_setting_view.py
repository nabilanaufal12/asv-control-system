# gui/views/servo_setting_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import Qt

class ServoSettingView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        # --- MODIFIKASI: Margin diperkecil dari 20 menjadi 10 ---
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setAlignment(Qt.AlignTop)

        servo_group = QGroupBox("Servo Angle Limits")
        form_layout = QFormLayout()

        self.left_max_input = QLineEdit("120")
        self.right_max_input = QLineEdit("60")

        form_layout.addRow("Max Left Angle (°):", self.left_max_input)
        form_layout.addRow("Max Right Angle (°):", self.right_max_input)
        
        save_button = QPushButton("Save Servo Settings")
        save_button.clicked.connect(self.save_servo_settings)

        layout_in_group = QVBoxLayout()
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(save_button)
        servo_group.setLayout(layout_in_group)
        
        main_layout.addWidget(servo_group)
        main_layout.addStretch()

    def save_servo_settings(self):
        left = self.left_max_input.text()
        right = self.right_max_input.text()
        print(f"--- Servo Settings Saved ---")
        print(f"Max Left: {left}°, Max Right: {right}°")