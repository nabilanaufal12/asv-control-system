# gui/views/status_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QHBoxLayout, QPushButton,
                             QLineEdit, QFormLayout) # Import QLineEdit dan QFormLayout
from PyQt5.QtCore import Qt, QTimer

class StatusPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15) # Tambahkan spasi antar grup utama

        # --- Waypoints Group ---
        wp_group = QGroupBox("Waypoints")
        wp_layout = QVBoxLayout()
        wp_layout.setSpacing(10)

        # NEW: Input Fields for Latitude and Longitude
        self.wp_form_layout = QFormLayout()
        self.lat_input = QLineEdit("-6.2100") # Default dummy value
        self.lon_input = QLineEdit("106.8400") # Default dummy value
        self.wp_form_layout.addRow("Latitude:", self.lat_input)
        self.wp_form_layout.addRow("Longitude:", self.lon_input)
        wp_layout.addLayout(self.wp_form_layout)

        # NEW: Add, Delete, Send All Buttons
        self.wp_buttons_layout = QHBoxLayout()
        self.add_wp_button = QPushButton("Add")
        self.add_wp_button.clicked.connect(self.add_waypoint)
        self.delete_wp_button = QPushButton("Delete")
        self.delete_wp_button.clicked.connect(self.delete_selected_waypoint)
        self.delete_wp_button.setEnabled(False) # Nonaktifkan secara default
        self.send_all_wp_button = QPushButton("Send All")
        self.send_all_wp_button.clicked.connect(self.send_all_waypoints)
        
        self.wp_buttons_layout.addWidget(self.add_wp_button)
        self.wp_buttons_layout.addWidget(self.delete_wp_button)
        self.wp_buttons_layout.addWidget(self.send_all_wp_button)
        wp_layout.addLayout(self.wp_buttons_layout)

        # Waypoint List (QListWidget) - Diubah posisinya
        self.wp_list = QListWidget()
        self.wp_list.setSelectionMode(QListWidget.SingleSelection) # Memungkinkan pemilihan satu item
        self.wp_list.itemSelectionChanged.connect(self._update_delete_button_state) # Update delete button

        # Tambahkan beberapa dummy waypoints awal
        self.add_waypoint_to_list("-6.2088", "106.8456")
        self.add_waypoint_to_list("-6.2095", "106.8470")
        self.add_waypoint_to_list("-6.2102", "106.8485")
        
        wp_layout.addWidget(self.wp_list)

        # Hapus tombol "Go to Selected Waypoint" dari sini, atau ganti logikanya ke "Send All"
        # Karena gambar baru tidak menunjukkannya secara eksplisit, saya akan menghapusnya
        # self.go_to_wp_button = QPushButton("Go to Selected Waypoint")
        # self.go_to_wp_button.clicked.connect(self.go_to_selected_waypoint)
        # self.go_to_wp_button.setEnabled(False)
        # self.wp_list.itemSelectionChanged.connect(self._update_go_to_wp_button_state)
        # wp_layout.addWidget(self.go_to_wp_button)

        wp_group.setLayout(wp_layout)
        self.main_layout.addWidget(wp_group)

        # --- System Status Group (tetap seperti sebelumnya, hanya memastikan objectName) ---
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8) # Sesuaikan spasi

        def create_status_label_pair(title, initial_value, object_name=None):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(title))
            value_label = QLabel(initial_value)
            value_label.setAlignment(Qt.AlignRight)
            if object_name:
                value_label.setObjectName(object_name)
            h_layout.addWidget(value_label)
            return h_layout, value_label

        self.gps_layout, self.gps_value_label = create_status_label_pair("GPS:", "12 Sats", "ValueLabel")
        self.battery_layout, self.battery_value_label = create_status_label_pair("Battery:", "11.9 V", "ValueLabel")
        self.compass_layout, self.compass_value_label = create_status_label_pair("Compass:", "295°", "ValueLabel")
        self.speed_layout, self.speed_value_label = create_status_label_pair("Speed:", "2.5 m/s", "ValueLabel")
        self.depth_layout, self.depth_value_label = create_status_label_pair("Depth:", "8.9 m", "ValueLabel")

        status_layout.addLayout(self.gps_layout)
        status_layout.addLayout(self.battery_layout)
        status_layout.addLayout(self.compass_layout)
        status_layout.addLayout(self.speed_layout)
        status_layout.addLayout(self.depth_layout)

        status_layout.addSpacing(10)
        status_layout.addWidget(QLabel("--- Communication ---"))

        self.radio_layout, self.radio_value_label = create_status_label_pair("Radio Link:", "Connected", "ValueLabel")
        self.telemetry_layout, self.telemetry_value_label = create_status_label_pair("Telemetry:", "Receiving", "ValueLabel")
        self.data_rate_layout, self.data_rate_value_label = create_status_label_pair("Data Rate:", "316 B/s", "ValueLabel")

        status_layout.addLayout(self.radio_layout)
        status_layout.addLayout(self.telemetry_layout)
        status_layout.addLayout(self.data_rate_layout)

        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)

        self.main_layout.addStretch()

        self._dummy_update_timer = QTimer(self)
        self._dummy_update_timer.timeout.connect(self._update_dummy_values)
        self._dummy_update_timer.start(1000)

    # NEW: Helper method to add waypoint to list
    def add_waypoint_to_list(self, lat, lon):
        item_text = f"WP {self.wp_list.count() + 1}: Lat {lat}, Lon {lon}"
        self.wp_list.addItem(QListWidgetItem(item_text))

    def add_waypoint(self):
        """Menambahkan waypoint baru dari input Lat/Lon ke daftar."""
        lat = self.lat_input.text()
        lon = self.lon_input.text()

        if lat and lon:
            # Validasi dasar (opsional, bisa lebih kompleks)
            try:
                float(lat)
                float(lon)
                self.add_waypoint_to_list(lat, lon)
                self.lat_input.clear()
                self.lon_input.clear()
                print(f"Added Waypoint: Lat {lat}, Lon {lon}")
            except ValueError:
                print("Invalid Latitude or Longitude format. Please enter numbers.")
        else:
            print("Latitude and Longitude cannot be empty.")

    def delete_selected_waypoint(self):
        """Menghapus waypoint yang dipilih dari daftar."""
        selected_items = self.wp_list.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.wp_list.row(item)
                self.wp_list.takeItem(row)
                print(f"Deleted Waypoint: {item.text()}")
            self._relabel_waypoints() # Relabel waypoints after deletion
        else:
            print("No waypoint selected to delete.")

    def _relabel_waypoints(self):
        """Updates waypoint numbers after deletion."""
        for i in range(self.wp_list.count()):
            item = self.wp_list.item(i)
            # Ambil hanya bagian Lat/Lon dari teks
            current_text_parts = item.text().split(': ', 1)
            if len(current_text_parts) > 1:
                item.setText(f"WP {i + 1}: {current_text_parts[1]}")
            else: # Fallback if format is unexpected
                item.setText(f"WP {i + 1}: {item.text()}")


    def send_all_waypoints(self):
        """Mengirim semua waypoint di daftar ke ASV."""
        if self.wp_list.count() == 0:
            print("No waypoints to send.")
            return

        waypoints_data = []
        for i in range(self.wp_list.count()):
            item = self.wp_list.item(i)
            # Contoh parsing text ke Lat/Lon. Perlu validasi lebih robust di aplikasi nyata.
            parts = item.text().split(': ')
            if len(parts) > 1 and 'Lat' in parts[1] and 'Lon' in parts[1]:
                lat_lon_str = parts[1].replace('Lat ', '').replace('Lon ', '')
                lat, lon = lat_lon_str.split(', ')
                waypoints_data.append({"lat": float(lat), "lon": float(lon)})
            else:
                print(f"Warning: Could not parse waypoint format for '{item.text()}'. Skipping.")
        
        if waypoints_data:
            print(f"Sending {len(waypoints_data)} waypoints to ASV: {waypoints_data}")
            # Di sini Anda akan menambahkan logika untuk mengirim array waypoints ke ASV
            # Misalnya: self.controller.send_waypoints_to_asv(waypoints_data)
        else:
            print("No valid waypoints found to send.")


    def _update_delete_button_state(self):
        """Updates the enabled state of the 'Delete' button."""
        self.delete_wp_button.setEnabled(len(self.wp_list.selectedItems()) > 0)


    def _update_dummy_values(self):
        # ... (fungsi dummy update sensor Anda tetap sama) ...
        import random
        self.gps_value_label.setText(f"{random.randint(8, 15)} Sats")
        self.battery_value_label.setText(f"{random.uniform(11.0, 12.8):.1f} V")
        self.compass_value_label.setText(f"{random.randint(0, 359)}°")
        self.speed_value_label.setText(f"{random.uniform(0.0, 3.5):.1f} m/s")
        self.depth_value_label.setText(f"{random.uniform(0.0, 10.0):.1f} m")
        self.radio_value_label.setText("Connected" if random.random() > 0.1 else "Disconnected")
        self.telemetry_value_label.setText("Receiving" if random.random() > 0.1 else "No Data")
        self.data_rate_value_label.setText(f"{random.randint(10, 500)} B/s")