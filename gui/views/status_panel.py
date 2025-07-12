# gui/views/status_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QHBoxLayout, QPushButton,
                             QLineEdit, QFormLayout, QScrollArea) # Tambahkan import QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator

class StatusPanel(QWidget):
    """
    Panel di sisi kanan aplikasi yang menampilkan status sistem secara real-time
    dan menyediakan fungsionalitas untuk manajemen waypoint.
    Kini menggunakan QScrollArea agar responsif terhadap perubahan ukuran jendela.
    """
    message_to_show = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Layout Utama & Scroll Area (MODIFIKASI UTAMA) ---
        # 1. Buat layout terluar untuk menampung QScrollArea.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. Buat QScrollArea untuk membuat konten dapat di-scroll.
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True) # Penting! Agar widget di dalamnya bisa mengisi area.
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Matikan scroll horizontal.
        
        # 3. Buat widget konten yang akan menjadi 'kanvas' di dalam scroll area.
        self.scroll_content_widget = QWidget()
        
        # 4. Gunakan self.main_layout sebagai layout untuk widget konten.
        # Semua elemen (GroupBox, dll.) akan ditambahkan ke layout ini.
        self.main_layout = QVBoxLayout(self.scroll_content_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # --- Grup Waypoints ---
        # (Tidak ada perubahan di dalam grup ini, hanya dipindahkan ke dalam main_layout)
        wp_group = QGroupBox("Waypoints")
        wp_layout = QVBoxLayout(wp_group)
        
        wp_form_layout = QFormLayout()
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        
        lat_validator = QDoubleValidator(-90.0, 90.0, 7, self)
        lon_validator = QDoubleValidator(-180.0, 180.0, 7, self)
        self.lat_input.setValidator(lat_validator)
        self.lon_input.setValidator(lon_validator)
        self.lat_input.setPlaceholderText("contoh: -6.2100")
        self.lon_input.setPlaceholderText("contoh: 106.8400")
        
        wp_form_layout.addRow("Latitude:", self.lat_input)
        wp_form_layout.addRow("Longitude:", self.lon_input)
        wp_layout.addLayout(wp_form_layout)
        
        wp_buttons_layout = QHBoxLayout()
        self.add_wp_button = QPushButton("Add")
        self.delete_wp_button = QPushButton("Delete")
        self.send_all_wp_button = QPushButton("Send All")
        
        self.add_wp_button.clicked.connect(self.add_waypoint)
        self.delete_wp_button.clicked.connect(self.delete_selected_waypoint)
        self.send_all_wp_button.clicked.connect(self.send_all_waypoints)
        
        wp_buttons_layout.addWidget(self.add_wp_button)
        wp_buttons_layout.addWidget(self.delete_wp_button)
        wp_buttons_layout.addWidget(self.send_all_wp_button)
        wp_layout.addLayout(wp_buttons_layout)
        
        self.wp_list = QListWidget()
        self.wp_list.itemSelectionChanged.connect(self._update_delete_button_state)
        wp_layout.addWidget(self.wp_list)
        
        wp_group.setLayout(wp_layout)
        self.main_layout.addWidget(wp_group) # Tambahkan grup ke main_layout

        # --- Grup Status Sistem ---
        # (Tidak ada perubahan di dalam grup ini)
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        
        def create_status_label_pair(title, initial_value):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(title))
            value_label = QLabel(initial_value)
            value_label.setAlignment(Qt.AlignRight)
            value_label.setObjectName("ValueLabel")
            h_layout.addWidget(value_label)
            return h_layout, value_label
            
        sensor_status_items = [
            create_status_label_pair("GPS:", "N/A"),
            create_status_label_pair("Battery:", "N/A"),
            create_status_label_pair("Compass:", "N/A"),
            create_status_label_pair("Speed:", "N/A"),
        ]
        for layout, _ in sensor_status_items:
            status_layout.addLayout(layout)
            
        steering_layout, self.auto_steering_label = create_status_label_pair("Auto-Steering:", "N/A")
        status_layout.addLayout(steering_layout)
        
        status_layout.addSpacing(10)
        status_layout.addWidget(QLabel("--- Communication ---"))
        
        comm_status_items = [
            create_status_label_pair("Radio Link:", "N/A"),
            create_status_label_pair("Telemetry:", "N/A"),
        ]
        for layout, _ in comm_status_items:
            status_layout.addLayout(layout)
            
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group) # Tambahkan grup ke main_layout
        
        # --- Finalisasi Layout ---
        self.main_layout.addStretch() # Mendorong semua grup ke atas
        
        # 5. Atur widget konten sebagai widget untuk scroll area.
        self.scroll_area.setWidget(self.scroll_content_widget)
        
        # 6. Tambahkan scroll area ke layout terluar.
        outer_layout.addWidget(self.scroll_area)
        
        self._update_delete_button_state()

    # (Sisa fungsi lainnya: add_waypoint, delete_selected_waypoint, dll. tidak berubah)
    def add_waypoint(self):
        lat = self.lat_input.text().strip().replace(',', '.')
        lon = self.lon_input.text().strip().replace(',', '.')
        if lat and lon:
            item_text = f"WP {self.wp_list.count() + 1}: Lat {lat}, Lon {lon}"
            self.wp_list.addItem(QListWidgetItem(item_text))
            self.lat_input.clear()
            self.lon_input.clear()
            self.message_to_show.emit(f"Waypoint {self.wp_list.count()} added!", 3000)
        else:
            self.message_to_show.emit("Latitude and Longitude cannot be empty.", 3000)

    def delete_selected_waypoint(self):
        selected_item = self.wp_list.currentItem()
        if selected_item:
            row = self.wp_list.row(selected_item)
            self.wp_list.takeItem(row)
            self._relabel_waypoints()
            self.message_to_show.emit("Waypoint deleted.", 3000)

    def send_all_waypoints(self):
        count = self.wp_list.count()
        if count == 0:
            self.message_to_show.emit("No waypoints to send.", 3000)
            return
        print(f"Sending {count} waypoints to ASV...")
        self.message_to_show.emit(f"Sent {count} waypoints to ASV.", 4000)

    def _relabel_waypoints(self):
        for i in range(self.wp_list.count()):
            item = self.wp_list.item(i)
            text_parts = item.text().split(': ', 1)
            if len(text_parts) > 1:
                item.setText(f"WP {i + 1}: {text_parts[1]}")

    def _update_delete_button_state(self):
        self.delete_wp_button.setEnabled(len(self.wp_list.selectedItems()) > 0)

    def update_auto_steering_degree(self, degree):
        self.auto_steering_label.setText(f"{degree}°")