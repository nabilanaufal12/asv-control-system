# gui/views/pid_view.py

# Impor pustaka yang diperlukan
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal # Impor pyqtSignal
# Impor untuk grafik
import pyqtgraph as pg
from collections import deque

class PidView(QWidget):
    """
    Widget tab untuk menampilkan dan mengatur parameter PID,
    serta menampilkan grafik respons sistem secara real-time.
    """
    # === DEFINISI SINYAL BARU ===
    # Sinyal untuk mengirim nilai P, I, D yang baru ke ControlPanel
    pid_gains_changed = pyqtSignal(float, float, float)
    # Sinyal untuk menampilkan pesan di status bar utama
    message_to_show = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        gains_group = QGroupBox("PID Controller Gains")
        form_layout = QFormLayout()
        # Atur nilai awal sesuai dengan yang ada di ControlPanel
        self.p_input = QLineEdit("0.5")
        self.i_input = QLineEdit("0.01")
        self.d_input = QLineEdit("0.1")
        form_layout.addRow("Proportional (P):", self.p_input)
        form_layout.addRow("Integral (I):", self.i_input)
        form_layout.addRow("Derivative (D):", self.d_input)
        
        self.save_button = QPushButton("Save PID Configuration")
        # Hubungkan tombol save ke fungsi logikanya
        self.save_button.clicked.connect(self.save_pid_config)
        
        layout_in_group = QVBoxLayout(gains_group)
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.save_button)
        main_layout.addWidget(gains_group)

        # (Kode untuk grafik tidak berubah)
        graph_group = QGroupBox("PID Response Graph")
        graph_layout = QVBoxLayout(graph_group)
        pg.setConfigOption('background', '#2c313a')
        pg.setConfigOption('foreground', '#abb2bf')
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setFixedHeight(300)
        self.plot_widget.setLabel('left', 'Angle (Degrees)')
        self.plot_widget.setLabel('bottom', 'Time (Updates)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(0, 180)
        self.setpoint_curve = self.plot_widget.plot(pen=pg.mkPen('g', width=2, style=Qt.DotLine), name="Setpoint (Target)")
        self.pv_curve = self.plot_widget.plot(pen=pg.mkPen('#0053A0', width=2), name="Actual Angle (Camera)")
        self.plot_widget.addLegend()
        graph_layout.addWidget(self.plot_widget)
        main_layout.addWidget(graph_group)

        self.time_data = deque(maxlen=100)
        self.setpoint_data = deque(maxlen=100)
        self.pv_data = deque(maxlen=100)
        self.time_counter = 0

    def save_pid_config(self):
        """
        Dipanggil saat tombol 'Save PID Configuration' ditekan.
        Membaca nilai dari input, memvalidasi, dan memancarkan sinyal.
        """
        try:
            # Baca teks dari input field dan konversi ke float
            kp = float(self.p_input.text().strip().replace(',', '.'))
            ki = float(self.i_input.text().strip().replace(',', '.'))
            kd = float(self.d_input.text().strip().replace(',', '.'))
            
            # Pancarkan sinyal dengan nilai-nilai yang baru
            self.pid_gains_changed.emit(kp, ki, kd)
            # Pancarkan sinyal untuk menampilkan pesan sukses
            self.message_to_show.emit("PID gains saved successfully!", 3000)
            
        except ValueError:
            # Jika input bukan angka, pancarkan pesan error
            self.message_to_show.emit("Invalid input. Please enter numbers for PID gains.", 4000)

    def update_graph(self, setpoint, process_variable):
        self.time_counter += 1
        self.time_data.append(self.time_counter)
        self.setpoint_data.append(setpoint)
        self.pv_data.append(process_variable)
        self.setpoint_curve.setData(list(self.time_data), list(self.setpoint_data))
        self.pv_curve.setData(list(self.time_data), list(self.pv_data))

