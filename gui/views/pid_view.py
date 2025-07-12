# gui/views/pid_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox
from PyQt5.QtCore import Qt

class PidView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        # --- MODIFIKASI: Margin diperkecil agar lebih ringkas ---
        main_layout.setContentsMargins(10, 10, 10, 10) 
        main_layout.setAlignment(Qt.AlignTop)

        # PID Settings Group
        pid_group = QGroupBox("PID Controller Gains")
        form_layout = QFormLayout()
        # --- MODIFIKASI: Kurangi spasi antar baris di form ---
        form_layout.setVerticalSpacing(10)
        
        self.p_input = QLineEdit("1.2")
        self.i_input = QLineEdit("0.5")
        self.d_input = QLineEdit("0.1")
        
        form_layout.addRow("Proportional (P):", self.p_input)
        form_layout.addRow("Integral (I):", self.i_input)
        form_layout.addRow("Derivative (D):", self.d_input)

        save_button = QPushButton("Save PID Configuration")
        save_button.clicked.connect(self.save_pid_config)
        
        layout_in_group = QVBoxLayout()
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(save_button)
        pid_group.setLayout(layout_in_group)
        
        # PID Response Graph Placeholder
        graph_placeholder = QLabel("PID Response Graph Placeholder")
        graph_placeholder.setAlignment(Qt.AlignCenter)
        # --- MODIFIKASI: Tinggi minimum dikurangi drastis dari 200 menjadi 80 ---
        # Ini adalah perubahan paling signifikan untuk menghemat ruang vertikal.
        graph_placeholder.setMinimumHeight(80) 
        graph_placeholder.setStyleSheet("background-color: #101020; border: 1px solid #3a3a5a; border-radius: 8px;")

        main_layout.addWidget(pid_group)
        # --- MODIFIKASI: Spasi antar grup dikurangi dari 20 menjadi 10 ---
        main_layout.addSpacing(10) 
        main_layout.addWidget(graph_placeholder)
        main_layout.addStretch()

    def save_pid_config(self):
        p = self.p_input.text()
        i = self.i_input.text()
        d = self.d_input.text()
        print(f"--- PID Config Saved ---")
        print(f"P: {p}, I: {i}, D: {d}")