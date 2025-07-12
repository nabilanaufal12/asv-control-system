# gui/views/status_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QHBoxLayout, QPushButton,
                             QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import re # Impor pustaka Regular Expression untuk parsing teks

class StatusPanel(QWidget):
    message_to_show = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # --- Grup Waypoints ---
        wp_group = QGroupBox("Waypoints")
        wp_layout = QVBoxLayout(wp_group)
        wp_form_layout = QFormLayout()
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        lat_validator = QDoubleValidator(-90.0, 90.0, 7, self)
        lon_validator = QDoubleValidator(-180.0, 180.0, 7, self)
        self.lat_input.setValidator(lat_validator)
        self.lon_input.setValidator(lon_validator)
        self.lat_input.setPlaceholderText("e.g., -6.2100")
        self.lon_input.setPlaceholderText("e.g., 106.8400")
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
        self.main_layout.addWidget(wp_group)

        # --- Grup Status Sistem ---
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)

        def create_status_label_pair(title, initial_value="---"):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(title))
            value_label = QLabel(initial_value)
            value_label.setAlignment(Qt.AlignRight)
            value_label.setObjectName("ValueLabel")
            h_layout.addWidget(value_label)
            return h_layout, value_label

        # === PERUBAHAN: Simpan referensi ke setiap label nilai ===
        gps_layout, self.gps_value_label = create_status_label_pair("GPS:")
        battery_layout, self.battery_value_label = create_status_label_pair("Battery:")
        compass_layout, self.compass_value_label = create_status_label_pair("Compass:")
        speed_layout, self.speed_value_label = create_status_label_pair("Speed:")
        steering_layout, self.auto_steering_label = create_status_label_pair("Auto-Steering:")
        
        status_layout.addLayout(gps_layout)
        status_layout.addLayout(battery_layout)
        status_layout.addLayout(compass_layout)
        status_layout.addLayout(speed_layout)
        status_layout.addLayout(steering_layout)
        
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)
        self.main_layout.addStretch()
        self._update_delete_button_state()

    # === FUNGSI BARU UNTUK MENDAPATKAN WAYPOINTS ===
    def get_waypoints(self):
        """Mengurai teks dari QListWidget dan mengembalikan daftar koordinat."""
        waypoints = []
        for i in range(self.wp_list.count()):
            item_text = self.wp_list.item(i).text()
            # Gunakan regular expression untuk mencari angka desimal (termasuk negatif)
            coords = re.findall(r"-?\d+\.\d+", item_text)
            if len(coords) == 2:
                try:
                    lat = float(coords[0])
                    lon = float(coords[1])
                    waypoints.append({'lat': lat, 'lon': lon})
                except ValueError:
                    continue # Abaikan jika konversi gagal
        return waypoints
        
    def update_gps(self, lat, lon, sats):
        self.gps_value_label.setText(f"{lat}, {lon} ({sats} Sats)")

    def update_battery(self, voltage):
        self.battery_value_label.setText(f"{voltage} V")

    def update_compass(self, degrees):
        self.compass_value_label.setText(f"{degrees}°")

    def update_speed(self, speed):
        self.speed_value_label.setText(f"{speed} m/s")

    def update_auto_steering_degree(self, degree):
        self.auto_steering_label.setText(f"{degree}°")

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
