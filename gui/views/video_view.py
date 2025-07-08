# gui/views/video_view.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolov5")))

import pathlib
pathlib.PosixPath = pathlib.WindowsPath

import cv2
import torch
import numpy as np


from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QImage, QPixmap

from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

class VideoView(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(False) # Tetap FALSE. Kita skala manual.

        self.video_layout = QVBoxLayout(self)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setSpacing(0)

        # --- Bagian Kontrol Kamera (Tombol Start/Stop) ---
        self.control_buttons_layout = QHBoxLayout()
        self.start_stop_button = QPushButton("Start Camera")
        self.start_stop_button.clicked.connect(self.toggle_camera)
        self.control_buttons_layout.addStretch()
        self.control_buttons_layout.addWidget(self.start_stop_button)
        self.control_buttons_layout.addStretch()

        self.video_layout.addLayout(self.control_buttons_layout)
        self.video_layout.addWidget(self.label)
        self.setLayout(self.video_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Inisialisasi variabel kamera dan timer
        self.cap = None
        self.timer = None
        self.is_camera_active = False

        # Load YOLOv5 model
        self.device = select_device('')
        try:
            # Perhatikan: pastikan path 'assets/best.pt' benar relatif terhadap main.py
            self.model = DetectMultiBackend('assets/best.pt', device=self.device, dnn=False)
            self.model.warmup(imgsz=(1, 3, 640, 640))
            self.names = self.model.names
            self.yolo_loaded = True
        except Exception as e:
            print(f"Warning: YOLOv5 model 'assets/best.pt' not found or failed to load: {e}. Video will be displayed without detection.")
            self.yolo_loaded = False
            self.label.setText("YOLOv5 Model not found. Click 'Start Camera'.")
            self.label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")


        self.original_frame_width = 0
        self.original_frame_height = 0
        self.aspect_ratio = 1.0

        self.label.setMinimumSize(400, 300) # Ukuran placeholder awal


    def toggle_camera(self):
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        if self.is_camera_active:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open video stream (webcam).")
            self.label.setText("Error: Could not open video stream (webcam).")
            self.label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            self.cap = None
            return

        self.original_frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.original_frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self.original_frame_width == 0 or self.original_frame_height == 0:
            print("Warning: Could not get valid camera resolution. Defaulting to 640x480 for aspect ratio.")
            self.original_frame_width = 640
            self.original_frame_height = 480
        
        self.aspect_ratio = self.original_frame_width / self.original_frame_height

        self.label.clear()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.is_camera_active = True
        self.start_stop_button.setText("Stop Camera")
        print("Camera started.")
        self.adjust_label_pixmap_size()

    def stop_camera(self):
        if not self.is_camera_active:
            return

        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.timer = None
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

        self.is_camera_active = False
        self.start_stop_button.setText("Start Camera")
        self.label.clear()
        self.label.setText("Camera Stopped.")
        self.label.setStyleSheet("color: #abb2bf; font-weight: normal; font-size: 14px;")
        print("Camera stopped.")

    def update_frame(self):
        if not self.is_camera_active or not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Warning: Failed to read frame from camera. Stopping camera.")
            self.stop_camera()
            return

        display_frame = frame.copy() # Gunakan salinan untuk menggambar deteksi

        if self.yolo_loaded:
            # --- Bagian Integrasi YOLOv5 dari deded1.py ---
            img = cv2.resize(frame, (640, 640))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_rgb).to(self.device)
            img_tensor = img_tensor.permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)

            with torch.no_grad():
                pred = self.model(img_tensor, augment=False, visualize=False)
                pred = non_max_suppression(pred, conf_thres=0.4, iou_thres=0.45)

            red_centers = []
            green_centers = []

            for det in pred:
                if len(det):
                    det[:, :4] = scale_boxes(img_tensor.shape[2:], det[:, :4], frame.shape).round()

                    for *xyxy, conf, cls in det:
                        class_name = self.names[int(cls)] # Gunakan self.names
                        x1, y1, x2, y2 = map(int, xyxy)
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                        if class_name == "Red_Ball":
                            red_centers.append((cx, cy))
                            color = (0, 0, 255) # BGR for OpenCV
                        elif class_name == "Green_Ball":
                            green_centers.append((cx, cy))
                            color = (0, 255, 0) # BGR for OpenCV
                        else:
                            continue

                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.circle(display_frame, (cx, cy), 5, (255, 255, 255), -1)
                        cv2.putText(display_frame, f"{class_name}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Urutkan dari bawah ke atas (karena y lebih besar ke bawah)
            red_centers.sort(key=lambda pt: -pt[1])
            green_centers.sort(key=lambda pt: -pt[1])

            midpoint = None
            current_degree = 0 # Inisialisasi

            if red_centers and green_centers:
                red_nearest = red_centers[0]
                green_nearest = green_centers[0]

                mx = (red_nearest[0] + green_nearest[0]) // 2
                my = (red_nearest[1] + green_nearest[1]) // 2
                midpoint = (mx, my)

                cv2.line(display_frame, red_nearest, green_nearest, (200, 200, 200), 2)
                cv2.circle(display_frame, midpoint, 6, (255, 0, 255), -1)
                cv2.putText(display_frame, "Midpoint", (mx - 40, my - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

            # Gambar skala 0–180 di bawah layar
            bar_y = display_frame.shape[0] - 100
            bar_left = 100
            bar_right = display_frame.shape[1] - 100
            bar_width = bar_right - bar_left
            bar_height = 40

            cv2.rectangle(display_frame, (bar_left, bar_y), (bar_right, bar_y + bar_height), (0, 140, 255), 2)
            center_x = (bar_left + bar_right) // 2
            cv2.line(display_frame, (center_x, bar_y), (center_x, bar_y + bar_height), (0, 140, 255), 2)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(display_frame, "0", (bar_left - 10, bar_y + bar_height + 30), font, 0.6, (0, 140, 255), 2)
            cv2.putText(display_frame, "90", (center_x - 15, bar_y + bar_height + 30), font, 0.6, (0, 140, 255), 2)
            cv2.putText(display_frame, "180", (bar_right - 30, bar_y + bar_height + 30), font, 0.6, (0, 140, 255), 2)

            # Kotak merah mengikuti midpoint
            if midpoint:
                midpoint_x = midpoint[0]
                relative = (midpoint_x - bar_left) / bar_width
                relative = np.clip(relative, 0, 1)

                current_degree = int(relative * 180) # Simpan derajat yang dihitung

                indicator_width = 40
                indicator_height = bar_height
                indicator_x = int(bar_left + relative * bar_width - indicator_width // 2)

                indicator_y = bar_y
                cv2.rectangle(display_frame, (indicator_x, indicator_y), (indicator_x + indicator_width, indicator_y + indicator_height), (0, 0, 255), -1)

                text = f"{current_degree} deg"
                text_size = cv2.getTextSize(text, font, 0.8, 2)[0]
                text_x = indicator_x + (indicator_width - text_size[0]) // 2
                text_y = indicator_y + indicator_height // 2 + text_size[1] // 2
                cv2.putText(display_frame, text, (text_x, text_y), font, 0.8, (255, 255, 255), 2)
            # --- Akhir Bagian Integrasi YOLOv5 dari deded1.py ---


        # Konversi frame yang sudah diproses ke QImage untuk ditampilkan di PyQt
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = display_frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(display_frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_image)
        
        # Penskalaan QPixmap agar sesuai dengan ukuran QLabel saat ini
        label_width = self.label.width()
        label_height = self.label.height()

        if label_width > 0 and label_height > 0:
            scaled_pixmap = pixmap.scaled(
                label_width, label_height,
                Qt.KeepAspectRatio, # Penting: Menjaga rasio aspek
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
        else:
            self.label.setPixmap(pixmap)


    def adjust_label_pixmap_size(self):
        self.update_frame()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_label_pixmap_size()


    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_label_pixmap_size()


    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)