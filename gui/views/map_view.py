# gui/views/map_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class MapView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder for a map. Later, this can be replaced with
        # a QtWebEngine widget loading Folium or another map library.
        map_placeholder = QLabel("Map View Placeholder\n(A QtWebEngine or similar widget will go here)")
        map_placeholder.setAlignment(Qt.AlignCenter)
        map_placeholder.setStyleSheet("background-color: #101020; border: 1px solid #3a3a5a; border-radius: 8px; font-size: 18px;")
        
        layout.addWidget(map_placeholder)