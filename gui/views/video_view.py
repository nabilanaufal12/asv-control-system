# gui/views/video_view.py

# --- Konfigurasi Path untuk YOLOv5 ---
# Menambahkan direktori yolov5 ke path sistem agar modul-modulnya bisa diimpor
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolov5")))

# --- Workaround untuk Path di Windows ---
# Mengatasi masalah kompatibilitas path antara sistem Posix (Linux/Mac) dan Windows
import pathlib
if os.name == 'nt': # Cek jika sistem operasi adalah Windows
    pathlib.PosixPath = pathlib.WindowsPath

# --- Impor Pustaka Utama ---
import cv2
import torch
import numpy as np

# --- Impor Pustaka PyQt5 ---
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, QSize, pyqtSignal # <<< PENTING: Impor pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# --- Impor dari YOLOv5 ---
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

class VideoView(QWidget):
    # === DEFINISI SINYAL ===
    # Membuat sinyal bernama 'degree_changed' yang akan membawa sebuah nilai integer (derajat).
    # Sinyal ini akan digunakan untuk mengirim data derajat dari VideoView ke widget lain (seperti ControlPanel).
    degree_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        # --- Variabel Status dan Inisialisasi ---
        self.is_camera_active = False
        self.yolo_loaded = False
        self.current_degree = 0 # Menyimpan nilai derajat terakhir yang terdeteksi
        self.cap = None
        self.timer = None
        
        # Inisialisasi label untuk menampilkan video
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(400, 300) # Ukuran placeholder

        # --- Tata Letak (Layout) ---
        self.start_stop_button = QPushButton("Start Camera")
        self.start_stop_button.clicked.connect(self.toggle_camera)
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        control_layout.addWidget(self.start_stop_button)
        control_layout.addStretch()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.label)
        
        # --- Memuat Model YOLOv5 ---
        try:
            self.device = select_device('')
            # Pastikan path 'assets/best.pt' benar relatif dari direktori utama proyek
            self.model = DetectMultiBackend('assets/best.pt', device=self.device, dnn=False)
            self.model.warmup(imgsz=(1, 3, 640, 640)) # Pemanasan model untuk performa lebih cepat
            self.names = self.model.names
            self.yolo_loaded = True
            print("Model YOLOv5 berhasil dimuat.")
        except Exception as e:
            self.yolo_loaded = False
            error_message = f"Gagal memuat model YOLOv5: {e}"
            print(f"Peringatan: {error_message}")
            self.label.setText(f"Model 'assets/best.pt' tidak ditemukan.\n{e}")
            self.label.setStyleSheet("color: red; font-weight: bold;")

    # --- Fungsi Kontrol Kamera ---

    def toggle_camera(self):
        """Menyalakan atau mematikan kamera."""
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        """Membuka stream video dari webcam dan memulai timer."""
        if self.is_camera_active: return
        self.cap = cv2.VideoCapture(0) # '0' untuk webcam default
        if not self.cap.isOpened():
            self.label.setText("Error: Tidak dapat membuka kamera.")
            self.cap = None
            return

        self.is_camera_active = True
        self.start_stop_button.setText("Stop Camera")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) # Update frame setiap 30 ms (~33 FPS)
        print("Kamera dimulai.")

    def stop_camera(self):
        """Menghentikan timer dan melepaskan sumber video."""
        if not self.is_camera_active: return
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        self.is_camera_active = False
        self.start_stop_button.setText("Start Camera")
        self.label.setText("Kamera Berhenti.")
        self.label.setStyleSheet("") # Reset style
        print("Kamera dihentikan.")

    # --- Fungsi Pemrosesan Frame ---

    def update_frame(self):
        """Membaca frame dari kamera, melakukan deteksi, dan menampilkannya."""
        if not self.is_camera_active or not self.cap: return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_camera()
            return
            
        display_frame = frame.copy()

        if self.yolo_loaded:
            # --- Logika Deteksi YOLOv5 ---
            # Pra-pemrosesan gambar untuk model
            img = cv2.resize(frame, (640, 640))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_rgb).to(self.device).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)

            # Lakukan prediksi
            with torch.no_grad():
                pred = self.model(img_tensor, augment=False, visualize=False)
                pred = non_max_suppression(pred, conf_thres=0.4, iou_thres=0.45)

            red_centers, green_centers = [], []

            # Proses hasil deteksi
            for det in pred:
                if len(det):
                    det[:, :4] = scale_boxes(img_tensor.shape[2:], det[:, :4], frame.shape).round()
                    for *xyxy, conf, cls in det:
                        class_name = self.names[int(cls)]
                        x1, y1, x2, y2 = map(int, xyxy)
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        # Kelompokkan berdasarkan kelas
                        if "Red" in class_name:
                            red_centers.append((cx, cy))
                            color = (0, 0, 255)
                        elif "Green" in class_name:
                            green_centers.append((cx, cy))
                            color = (0, 255, 0)
                        else: continue
                        
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # --- Logika Midpoint dan Perhitungan Derajat ---
            if red_centers and green_centers:
                # Ambil bola terdekat (asumsi y terbesar)
                red_nearest = max(red_centers, key=lambda pt: pt[1])
                green_nearest = max(green_centers, key=lambda pt: pt[1])

                # Hitung titik tengah (midpoint)
                mx = (red_nearest[0] + green_nearest[0]) // 2
                my = (red_nearest[1] + green_nearest[1]) // 2
                
                # Gambar garis dan titik tengah
                cv2.line(display_frame, red_nearest, green_nearest, (200, 200, 200), 2)
                cv2.circle(display_frame, (mx, my), 6, (255, 0, 255), -1)

                # Hitung posisi relatif midpoint pada frame
                frame_width = display_frame.shape[1]
                relative_position = np.clip(mx / frame_width, 0, 1) # Normalisasi ke 0-1
                
                # Konversi posisi relatif ke derajat (0-180)
                new_degree = int(relative_position * 180)

                # === EMIT SINYAL ===
                # Jika nilai derajat berubah dari frame sebelumnya, pancarkan (emit) sinyalnya.
                # Ini mencegah pengiriman data yang sama berulang kali dan lebih efisien.
                if new_degree != self.current_degree:
                    self.current_degree = new_degree
                    self.degree_changed.emit(self.current_degree) # <<< PENTING: Mengirim sinyal
                    
                # Tampilkan derajat pada layar
                cv2.putText(display_frame, f"Degree: {self.current_degree}", (mx, my - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)


        # --- Konversi Frame ke Tampilan PyQt ---
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = display_frame_rgb.shape
        q_image = QImage(display_frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        # Skalakan pixmap agar sesuai dengan ukuran label dengan menjaga rasio aspek
        scaled_pixmap = pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)

    # --- Event Handler ---
    
    def resizeEvent(self, event):
        """Dipanggil saat ukuran widget berubah, untuk menyesuaikan ukuran video."""
        super().resizeEvent(event)
        # Jika kamera aktif, panggil update_frame untuk redraw dengan ukuran baru
        if self.is_camera_active:
            self.update_frame()

    def closeEvent(self, event):
        """Memastikan kamera berhenti saat widget ditutup."""
        self.stop_camera()
        super().closeEvent(event)