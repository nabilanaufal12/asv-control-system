# gui/views/map_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout
# Impor QWebEngineView untuk menampilkan konten web (HTML)
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium
import io # Digunakan untuk menyimpan file HTML di memori

class MapView(QWidget):
    """
    Widget tab yang menampilkan peta interaktif menggunakan Folium dan QWebEngineView.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Pengaturan Layout ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Buat widget browser mini untuk menampilkan peta
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        # Tampilkan peta awal yang berpusat di Tanjung Pinang saat aplikasi pertama kali dibuka
        # Menggunakan koordinat yang lebih spesifik untuk Tanjung Pinang
        self.update_map(0.9200, 104.4400, [], 0)

    def update_map(self, asv_lat, asv_lon, waypoints, current_heading):
        """
        Membuat atau memperbarui peta dengan posisi ASV dan waypoints terbaru.

        Args:
            asv_lat (float): Lintang posisi ASV saat ini.
            asv_lon (float): Bujur posisi ASV saat ini.
            waypoints (list): Daftar dictionary waypoint, masing-masing berisi {'lat': ..., 'lon': ...}.
            current_heading (float): Arah kompas ASV saat ini (dalam derajat).
        """
        # Buat objek peta Folium, berpusat pada posisi ASV
        m = folium.Map(location=[asv_lat, asv_lon], zoom_start=17, tiles="OpenStreetMap")

        # === PERUBAHAN: Buat teks popup yang lebih informatif ===
        # Format teks HTML untuk popup dengan 6 angka di belakang koma untuk presisi.
        popup_text = f"""
        <b>ASV Position</b><br>
        Latitude: {asv_lat:.6f}<br>
        Longitude: {asv_lon:.6f}
        """

        # --- Tambahkan Marker untuk Posisi ASV ---
        # Gunakan ikon panah dan putar sesuai arah kompas
        asv_icon = folium.Icon(
            color='blue',       # Warna ikon
            icon_color='white',
            icon='arrow-up',    # Ikon panah dari pustaka Font Awesome
            prefix='fa',        # Tipe ikon
            angle=current_heading # Putar ikon sesuai arah kapal
        )
        folium.Marker(
            location=[asv_lat, asv_lon],
            # Gunakan teks popup yang sudah kita format
            popup=folium.Popup(popup_text, max_width=250),
            tooltip="ASV Position", # Teks yang muncul saat mouse hover
            icon=asv_icon
        ).add_to(m)

        # --- Tambahkan Marker dan Garis untuk Waypoints ---
        if waypoints:
            wp_coords = []
            for i, wp in enumerate(waypoints):
                wp_coords.append((wp['lat'], wp['lon']))
                # Tambahkan marker untuk setiap waypoint
                folium.Marker(
                    location=[wp['lat'], wp['lon']],
                    popup=f"Waypoint {i+1}<br>Lat: {wp['lat']:.6f}<br>Lon: {wp['lon']:.6f}",
                    icon=folium.Icon(color='green', icon='flag')
                ).add_to(m)
            
            # Gambar garis merah yang menghubungkan semua waypoint
            folium.PolyLine(wp_coords, color="#D42127", weight=2.5, opacity=1).add_to(m)

        # Simpan peta yang sudah jadi ke dalam buffer memori sebagai data HTML
        data = io.BytesIO()
        m.save(data, close_file=False)
        
        # Muat konten HTML tersebut ke dalam widget browser
        self.web_view.setHtml(data.getvalue().decode())

