# gui/views/pid_view.py

# Impor pustaka yang diperlukan
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import Qt
# Impor baru untuk grafik
import pyqtgraph as pg
from collections import deque

class PidView(QWidget):
    """
    Widget tab untuk menampilkan dan mengatur parameter PID,
    serta menampilkan grafik respons sistem secara real-time.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Pengaturan Layout Utama ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Grup untuk Input Gain PID ---
        gains_group = QGroupBox("PID Controller Gains")
        form_layout = QFormLayout()
        self.p_input = QLineEdit("1.2")
        self.i_input = QLineEdit("0.5")
        self.d_input = QLineEdit("0.1")
        form_layout.addRow("Proportional (P):", self.p_input)
        form_layout.addRow("Integral (I):", self.i_input)
        form_layout.addRow("Derivative (D):", self.d_input)
        
        self.save_button = QPushButton("Save PID Configuration")
        
        layout_in_group = QVBoxLayout(gains_group)
        layout_in_group.addLayout(form_layout)
        layout_in_group.addWidget(self.save_button)
        
        main_layout.addWidget(gains_group)

        # === Buat Widget Grafik ===
        graph_group = QGroupBox("PID Response Graph")
        graph_layout = QVBoxLayout(graph_group)
        
        # Konfigurasi tampilan grafik
        pg.setConfigOption('background', '#2c313a')
        pg.setConfigOption('foreground', '#abb2bf')

        self.plot_widget = pg.PlotWidget()
        
        # === PERUBAHAN: Atur tinggi tetap untuk grafik agar berbentuk persegi ===
        # Mengatur tinggi tetap akan membuat widget grafik tidak terlalu memanjang ke bawah.
        # Karena lebarnya dibatasi oleh panel kiri, ini akan menghasilkan bentuk yang lebih persegi.
        self.plot_widget.setFixedHeight(300) 
        
        self.plot_widget.setLabel('left', 'Angle (Degrees)')
        self.plot_widget.setLabel('bottom', 'Time (Updates)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(0, 180) # Atur rentang sumbu Y dari 0 hingga 180 derajat
        
        # Buat garis untuk data Setpoint (target) dan Process Variable (nilai aktual)
        self.setpoint_curve = self.plot_widget.plot(pen=pg.mkPen('g', width=2, style=Qt.DotLine), name="Setpoint (Target)")
        self.pv_curve = self.plot_widget.plot(pen=pg.mkPen('#0053A0', width=2), name="Actual Angle (Camera)")

        # Tambahkan legenda untuk membedakan garis
        self.plot_widget.addLegend()

        graph_layout.addWidget(self.plot_widget)
        main_layout.addWidget(graph_group) # Hapus stretch factor agar ukuran grup mengikuti kontennya

        # --- Penyimpanan Data untuk Grafik ---
        # Gunakan deque untuk efisiensi, simpan 100 data point terakhir
        self.time_data = deque(maxlen=100)
        self.setpoint_data = deque(maxlen=100)
        self.pv_data = deque(maxlen=100)
        self.time_counter = 0

    def update_graph(self, setpoint, process_variable):
        """
        Slot publik yang akan menerima data dari ControlPanel untuk di-plot.
        
        Args:
            setpoint (float): Nilai target (misal: 90 derajat).
            process_variable (float): Nilai aktual yang diukur (derajat dari kamera).
        """
        # Tambahkan data baru ke deque
        self.time_counter += 1
        self.time_data.append(self.time_counter)
        self.setpoint_data.append(setpoint)
        self.pv_data.append(process_variable)

        # Update data di kurva grafik
        self.setpoint_curve.setData(list(self.time_data), list(self.setpoint_data))
        self.pv_curve.setData(list(self.time_data), list(self.pv_data))
