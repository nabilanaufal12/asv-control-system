# gui/views/servo_setting_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal # Impor pyqtSignal

class ServoSettingView(QWidget):
    """
    Widget tab untuk mengatur batas pergerakan sudut servo.
    """
    # === DEFINISI SINYAL BARU ===
    # Sinyal untuk mengirim batas sudut kiri dan kanan yang baru
    servo_limits_changed = pyqtSignal(int, int)
    # Sinyal untuk menampilkan pesan di status bar
    message_to_show = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        settings_group = QGroupBox("Servo Angle Limits")
        form_layout = QFormLayout()
        
        # Nilai default untuk batas sudut
        self.max_left_input = QLineEdit("45") 
        self.max_right_input = QLineEdit("135")
        
        form_layout.addRow("Max Left Angle (°):", self.max_left_input)
        form_layout.addRow("Max Right Angle (°):", self.max_right_input)

        self.save_button = QPushButton("Save Servo Settings")
        # Hubungkan tombol ke fungsi logikanya
        self.save_button.clicked.connect(self.save_servo_settings)
        
        layout_in_group = QVBoxLayout(settings_group)
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.save_button)
        
        main_layout.addWidget(settings_group)
        main_layout.addStretch()

    def save_servo_settings(self):
        """
        Dipanggil saat tombol 'Save Servo Settings' ditekan.
        """
        try:
            # Baca dan konversi nilai ke integer
            left_limit = int(self.max_left_input.text().strip())
            right_limit = int(self.max_right_input.text().strip())
            
            # Validasi sederhana untuk memastikan nilai masuk akal
            if not (0 <= left_limit < 90 and 90 < right_limit <= 180):
                self.message_to_show.emit("Invalid limits. Left must be < 90, Right must be > 90.", 5000)
                return

            # Pancarkan sinyal dengan batas yang baru
            self.servo_limits_changed.emit(left_limit, right_limit)
            self.message_to_show.emit("Servo limits saved successfully!", 3000)

        except ValueError:
            # Jika input bukan angka, tampilkan error
            self.message_to_show.emit("Invalid input. Please enter whole numbers for servo limits.", 4000)
