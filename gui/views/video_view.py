# gui/views/video_view.py

# --- Konfigurasi Path untuk YOLOv5 ---
import sys
import os
# Menambahkan direktori yolov5 ke path sistem agar modul-modulnya bisa diimpor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolov5")))

# --- Workaround untuk Path di Windows ---
import pathlib
# Mengatasi masalah kompatibilitas path antara sistem Posix (Linux/Mac) dan Windows
if os.name == 'nt':
    pathlib.PosixPath = pathlib.WindowsPath

# --- Impor Pustaka Utama ---
import cv2
import torch
import numpy as np

# --- Impor Pustaka PyQt5 ---
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, QSize, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# --- Impor dari YOLOv5 ---
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

class VideoView(QWidget):
    """
    Widget yang bertanggung jawab untuk menampilkan stream video dari kamera,
    melakukan deteksi objek (bola merah & hijau) menggunakan YOLOv5,
    dan memancarkan sinyal berisi derajat kemudi yang dihitung.
    """
    # Definisikan sinyal yang akan memberitahu widget lain tentang perubahan derajat
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
        self.label = QLabel() # Label untuk menampilkan frame video
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(400, 300) # Ukuran awal placeholder

        self.start_stop_button = QPushButton("Start Camera")
        self.start_stop_button.clicked.connect(self.toggle_camera)
        
        # Layout untuk tombol agar berada di tengah
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        control_layout.addWidget(self.start_stop_button)
        control_layout.addStretch()
        
        # Layout utama untuk widget ini
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.label)
        
        # --- Memuat Model YOLOv5 ---
        try:
            self.device = select_device('') # Pilih device (CPU/GPU)
            # Muat model dari file .pt
            self.model = DetectMultiBackend('assets/best.pt', device=self.device, dnn=False)
            self.model.warmup(imgsz=(1, 3, 640, 640)) # Pemanasan model untuk inferensi lebih cepat
            self.names = self.model.names # Ambil nama-nama kelas (misal: "Red_Ball")
            self.yolo_loaded = True
            print("Model YOLOv5 berhasil dimuat.")
        except Exception as e:
            self.yolo_loaded = False
            error_message = f"Gagal memuat model YOLOv5: {e}"
            print(f"Peringatan: {error_message}")
            self.label.setText(f"Model 'assets/best.pt' tidak ditemukan.\n{e}")
            self.label.setStyleSheet("color: red; font-weight: bold;")

    def toggle_camera(self):
        """Menyalakan atau mematikan kamera berdasarkan status saat ini."""
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        """Membuka koneksi ke webcam dan memulai timer untuk update frame."""
        if self.is_camera_active: return
        self.cap = cv2.VideoCapture(0) # Buka webcam default
        if not self.cap.isOpened():
            self.label.setText("Error: Tidak dapat membuka kamera.")
            self.cap = None
            return
        self.is_camera_active = True
        self.start_stop_button.setText("Stop Camera")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame) # Hubungkan timer ke fungsi update_frame
        self.timer.start(30) # Atur timer untuk berjalan setiap 30 ms (~33 FPS)
        print("Kamera dimulai.")

    def stop_camera(self):
        """Menghentikan timer dan melepaskan koneksi ke webcam."""
        if not self.is_camera_active: return
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        self.is_camera_active = False
        self.start_stop_button.setText("Start Camera")
        self.label.setText("Kamera Berhenti.")
        self.label.setStyleSheet("") # Reset style

    def update_frame(self):
        """Fungsi utama yang dipanggil oleh timer untuk memproses setiap frame."""
        if not self.is_camera_active or not self.cap: return
        ret, frame = self.cap.read() # Baca satu frame dari kamera
        if not ret:
            self.stop_camera()
            return
        display_frame = frame.copy() # Buat salinan frame untuk digambari

        if self.yolo_loaded:
            # --- Logika Deteksi YOLOv5 ---
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
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        # Kelompokkan pusat objek berdasarkan kelasnya
                        if "Red" in class_name:
                            red_centers.append((cx, cy))
                            color = (0, 0, 255) # Merah dalam BGR
                        elif "Green" in class_name:
                            green_centers.append((cx, cy))
                            color = (0, 255, 0) # Hijau dalam BGR
                        else: continue
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # Hitung midpoint jika kedua jenis bola terdeteksi
            if red_centers and green_centers:
                red_nearest = max(red_centers, key=lambda pt: pt[1])
                green_nearest = max(green_centers, key=lambda pt: pt[1])
                mx = (red_nearest[0] + green_nearest[0]) // 2
                my = (red_nearest[1] + green_nearest[1]) // 2
                midpoint = (mx, my)
                cv2.line(display_frame, red_nearest, green_nearest, (200, 200, 200), 2)
                cv2.circle(display_frame, (mx, my), 6, (255, 0, 255), -1)

            # --- Bagian untuk menggambar skala derajat ---
            bar_y = display_frame.shape[0] - 50
            bar_left = 50
            bar_right = display_frame.shape[1] - 50
            bar_width = bar_right - bar_left
            bar_height = 20
            font = cv2.FONT_HERSHEY_SIMPLEX

            # Gambar elemen-elemen visual skala
            cv2.rectangle(display_frame, (bar_left, bar_y), (bar_right, bar_y + bar_height), (0, 140, 255), 2)
            center_x = (bar_left + bar_right) // 2
            cv2.line(display_frame, (center_x, bar_y), (center_x, bar_y + bar_height), (0, 140, 255), 2)
            cv2.putText(display_frame, "0", (bar_left - 10, bar_y + bar_height + 20), font, 0.5, (255, 255, 255), 2)
            cv2.putText(display_frame, "90", (center_x - 15, bar_y + bar_height + 20), font, 0.5, (255, 255, 255), 2)
            cv2.putText(display_frame, "180", (bar_right - 20, bar_y + bar_height + 20), font, 0.5, (255, 255, 255), 2)

            # Jika midpoint terdeteksi, hitung derajat dan gambar indikator
            if midpoint:
                midpoint_x = midpoint[0]
                relative_position = np.clip(midpoint_x / display_frame.shape[1], 0, 1)
                new_degree = int(relative_position * 180)

                # Gambar kotak indikator merah pada skala
                indicator_width = 30
                indicator_x = int(bar_left + relative_position * bar_width - indicator_width // 2)
                cv2.rectangle(display_frame, (indicator_x, bar_y), (indicator_x + indicator_width, bar_y + bar_height), (0, 0, 255), -1)

                # Tampilkan teks derajat di atas indikator
                text = f"{new_degree}°"
                text_size = cv2.getTextSize(text, font, 0.6, 2)[0]
                text_x = indicator_x + (indicator_width - text_size[0]) // 2
                text_y = bar_y - 10
                cv2.putText(display_frame, text, (text_x, text_y), font, 0.6, (0, 0, 255), 2)

                # Pancarkan sinyal jika nilai derajat berubah dari frame sebelumnya
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
