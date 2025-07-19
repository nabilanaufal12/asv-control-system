# gui/views/video_view.py

import sys
import os
# Menambahkan direktori yolov5 ke path sistem agar modul-modulnya bisa diimpor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolov5")))

import pathlib
# Mengatasi masalah kompatibilitas path antara sistem Posix (Linux/Mac) dan Windows
if os.name == 'nt':
    pathlib.PosixPath = pathlib.WindowsPath

import cv2
import torch
import numpy as np

# Impor pustaka PyQt5 yang diperlukan
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# Impor dari YOLOv5
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

class VideoView(QWidget):
    """
    Widget yang bertanggung jawab untuk menampilkan stream video,
    memungkinkan pemilihan sumber kamera, melakukan deteksi objek,
    dan memancarkan sinyal berisi sudut kemudi yang dihitung.
    """
    # Sinyal yang akan dipancarkan saat ada perubahan derajat dari deteksi objek
    degree_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Inisialisasi variabel status
        self.is_camera_active = False
        self.yolo_loaded = False
        self.current_degree = 0
        self.cap = None
        self.timer = None
        
        # --- Pengaturan UI ---
        self.label = QLabel("Camera is stopped. Select a source and click 'Start Camera'.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(400, 300)

        # Dropdown untuk pemilihan kamera
        self.camera_selector = QComboBox()
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.list_cameras)
        
        self.start_stop_button = QPushButton("Start Camera")
        self.start_stop_button.clicked.connect(self.toggle_camera)

        # Layout untuk kontrol di bagian atas (pemilihan kamera, tombol, dll.)
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Camera Source:"))
        control_layout.addWidget(self.camera_selector, 1) # Stretch factor 1 agar bisa memanjang
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.start_stop_button)
        
        # Layout utama untuk widget ini
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.label, 1) # Stretch factor 1 agar label video mengisi sisa ruang
        
        # --- Memuat Model YOLOv5 ---
        try:
            self.device = select_device('')
            self.model = DetectMultiBackend('assets/best.pt', device=self.device, dnn=False)
            self.model.warmup(imgsz=(1, 3, 640, 640)) # Pemanasan model untuk inferensi lebih cepat
            self.names = self.model.names
            self.yolo_loaded = True
            print("Model YOLOv5 berhasil dimuat.")
        except Exception as e:
            self.yolo_loaded = False
            self.label.setText(f"Model 'assets/best.pt' not found.\n{e}")
            self.label.setStyleSheet("color: red; font-weight: bold;")
            
        # Panggil fungsi untuk mengisi daftar kamera saat pertama kali aplikasi dibuka
        self.list_cameras()

    def list_cameras(self):
        """Mendeteksi semua kamera yang tersedia (termasuk DroidCam) dan mengisinya ke dropdown."""
        self.camera_selector.clear()
        index = 0
        available_cameras = []
        while True:
            # Coba buka kamera dengan indeks tertentu. Menghapus cv2.CAP_DSHOW
            # membiarkan OpenCV memilih backend terbaik yang tersedia, ini lebih tangguh.
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Jika berhasil dibuka, tambahkan ke daftar dan lepaskan kembali.
                available_cameras.append(f"Camera {index}")
                cap.release()
                index += 1
            else:
                # Jika gagal, berarti sudah tidak ada kamera lagi.
                cap.release()
                break
        
        if available_cameras:
            self.camera_selector.addItems(available_cameras)
        else:
            self.camera_selector.addItem("No cameras found")

    def toggle_camera(self):
        """Menyalakan atau mematikan kamera."""
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        """Membuka stream video dari kamera yang dipilih dan memulai timer."""
        if self.is_camera_active: return
        
        selected_index = self.camera_selector.currentIndex()
        if selected_index < 0:
            self.label.setText("No camera selected.")
            return

        self.cap = cv2.VideoCapture(selected_index)
        if not self.cap.isOpened():
            self.label.setText(f"Error: Could not open Camera {selected_index}.")
            self.cap = None
            return

        self.is_camera_active = True
        self.start_stop_button.setText("Stop Camera")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        print(f"Camera {selected_index} started.")

    def stop_camera(self):
        """Menghentikan timer dan melepaskan sumber video."""
        if not self.is_camera_active: return
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        self.is_camera_active = False
        self.start_stop_button.setText("Start Camera")
        self.label.setText("Camera is stopped.")
        self.label.setStyleSheet("")

    def update_frame(self):
        """Fungsi utama yang dipanggil oleh timer untuk memproses setiap frame."""
        if not self.is_camera_active or not self.cap: return
        ret, frame = self.cap.read()
        if not ret:
            self.stop_camera()
            return
        
        display_frame = frame.copy() # Buat salinan frame untuk digambari
        
        if self.yolo_loaded:
            # Pra-pemrosesan gambar agar sesuai dengan input model
            img = cv2.resize(frame, (640, 640))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_rgb).to(self.device).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)
            
            # Lakukan inferensi/prediksi
            with torch.no_grad():
                pred = self.model(img_tensor, augment=False, visualize=False)
                pred = non_max_suppression(pred, conf_thres=0.4, iou_thres=0.45)
            
            red_centers, green_centers = [], []
            midpoint = None
            
            # Proses setiap deteksi
            for det in pred:
                if len(det):
                    det[:, :4] = scale_boxes(img_tensor.shape[2:], det[:, :4], display_frame.shape).round()
                    for *xyxy, conf, cls in det:
                        class_name = self.names[int(cls)]
                        x1, y1, x2, y2 = map(int, xyxy)
                        # Kelompokkan pusat objek berdasarkan kelasnya dan gambar kotak
                        if "Red" in class_name:
                            red_centers.append(((x1 + x2) // 2, (y1 + y2) // 2))
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        elif "Green" in class_name:
                            green_centers.append(((x1 + x2) // 2, (y1 + y2) // 2))
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Hitung midpoint jika kedua jenis bola terdeteksi
            if red_centers and green_centers:
                red_nearest = max(red_centers, key=lambda pt: pt[1])
                green_nearest = max(green_centers, key=lambda pt: pt[1])
                midpoint = ((red_nearest[0] + green_nearest[0]) // 2, (red_nearest[1] + green_nearest[1]) // 2)
                cv2.line(display_frame, red_nearest, green_nearest, (200, 200, 200), 2)
                cv2.circle(display_frame, midpoint, 6, (255, 0, 255), -1)

            # --- Logika Penggambaran Skala Derajat ---
            bar_y = display_frame.shape[0] - 50
            bar_left = 50
            bar_right = display_frame.shape[1] - 50
            bar_width = bar_right - bar_left
            font = cv2.FONT_HERSHEY_SIMPLEX

            # Gambar elemen-elemen visual skala
            cv2.rectangle(display_frame, (bar_left, bar_y), (bar_right, bar_y + 20), (0, 140, 255), 2)
            center_x = (bar_left + bar_right) // 2
            cv2.line(display_frame, (center_x, bar_y), (center_x, bar_y + 20), (0, 140, 255), 2)
            cv2.putText(display_frame, "0", (bar_left - 10, bar_y + 40), font, 0.5, (255, 255, 255), 2)
            cv2.putText(display_frame, "90", (center_x - 15, bar_y + 40), font, 0.5, (255, 255, 255), 2)
            cv2.putText(display_frame, "180", (bar_right - 20, bar_y + 40), font, 0.5, (255, 255, 255), 2)
            
            # Jika midpoint terdeteksi, hitung derajat dan gambar indikator
            if midpoint:
                relative_position = np.clip(midpoint[0] / display_frame.shape[1], 0, 1)
                new_degree = int(relative_position * 180)
                indicator_x = int(bar_left + relative_position * bar_width - 15)
                cv2.rectangle(display_frame, (indicator_x, bar_y), (indicator_x + 30, bar_y + 20), (0, 0, 255), -1)
                text = f"{new_degree}°"
                text_size = cv2.getTextSize(text, font, 0.6, 2)[0]
                cv2.putText(display_frame, text, (indicator_x + (30 - text_size[0]) // 2, bar_y - 10), font, 0.6, (0, 0, 255), 2)
                
                # Pancarkan sinyal hanya jika nilai derajat berubah dari frame sebelumnya
                if new_degree != self.current_degree:
                    self.current_degree = new_degree
                    self.degree_changed.emit(self.current_degree)
        
        # --- Konversi Frame ke Tampilan PyQt ---
        # Konversi frame OpenCV (BGR) ke format yang bisa dibaca PyQt (RGB)
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = display_frame_rgb.shape
        q_image = QImage(display_frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        # Skalakan gambar agar sesuai dengan ukuran label sambil menjaga rasio aspek
        scaled_pixmap = pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Dipanggil saat ukuran widget berubah untuk menyesuaikan skala video."""
        super().resizeEvent(event)
        if self.is_camera_active:
            self.update_frame()

    def closeEvent(self, event):
        """Memastikan kamera berhenti saat widget ditutup."""
        self.stop_camera()
        super().closeEvent(event)
