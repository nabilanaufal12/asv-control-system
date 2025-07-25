# gui/views/video_view.py

import sys
import os
import cv2
import torch
import numpy as np
from pathlib import Path

if os.name == 'nt':
    import pathlib
    pathlib.PosixPath = pathlib.WindowsPath

# PENTING: Penambahan Path YOLOv5 yang Sangat Robust
CURRENT_FILE_DIR = Path(os.path.abspath(__file__)).resolve()
PROJECT_ROOT = CURRENT_FILE_DIR.parents[2]

YOLOV5_ROOT_PATH = PROJECT_ROOT / 'yolov5'
if str(YOLOV5_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(YOLOV5_ROOT_PATH))

# PENTING: Definisi TryExcept di sini (jika diperlukan oleh YOLOv5 Anda)
def TryExcept(*args, **kwargs):
    def try_except(func):
        def wrap_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return None
        return wrap_function
    return try_except if len(args) == 0 else try_except(args[0])

# Impor dari YOLOv5
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes # <<< NON_MAX_SUPPRESSION & SCALE_BOXES dari general
# <<< PENTING: select_device & smart_inference_mode dari torch_utils >>>
from utils.torch_utils import select_device, smart_inference_mode
from ultralytics.utils.plotting import Annotator, colors

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class VideoView(QWidget):
    degree_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_camera_active = False
        self.yolo_loaded = False
        self.current_degree = 0
        self.cap = None
        self.timer = None
        
        self.label = QLabel("Camera is stopped. Select a source and click 'Start Camera'.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(400, 300)

        self.camera_selector = QComboBox()
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.list_cameras)
        
        self.start_stop_button = QPushButton("Start Camera")
        self.start_stop_button.clicked.connect(self.toggle_camera)

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Camera Source:"))
        control_layout.addWidget(self.camera_selector, 1)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.start_stop_button)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.label, 1)
        
        try:
            self.device = select_device('')
            model_path = str(YOLOV5_ROOT_PATH / "best.pt")
            self.model = DetectMultiBackend(model_path, device=self.device, dnn=False)
            self.model.warmup(imgsz=(1, 3, 640, 640))
            self.names = self.model.names
            self.yolo_loaded = True
            print(f"Model YOLOv5 berhasil dimuat dari: {model_path}")
        except Exception as e:
            self.yolo_loaded = False
            self.label.setText(f"Model 'best.pt' not found or failed to load:\n{e}\nClick 'Start Camera' for video only.")
            self.label.setStyleSheet("color: red; font-weight: bold;")
            print(f"Error memuat model YOLOv5: {e}")
            
        self.list_cameras()

    def list_cameras(self):
        self.camera_selector.clear()
        available_cameras = []
        for index in range(10): 
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                available_cameras.append(f"Camera {index}")
                cap.release()
            else:
                cap.release()
        
        if available_cameras:
            self.camera_selector.addItems(available_cameras)
            self.start_stop_button.setEnabled(True)
        else:
            self.camera_selector.addItem("No cameras found")
            self.start_stop_button.setEnabled(False)
            self.label.setText("No cameras found. Connect a camera.")
            self.label.setStyleSheet("color: orange; font-weight: bold;")

    def toggle_camera(self):
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        if self.is_camera_active: return
        
        selected_text = self.camera_selector.currentText()
        if "Camera" in selected_text:
            selected_index = int(selected_text.split(" ")[1])
        else:
            self.label.setText("Please select a valid camera source.")
            return

        self.cap = cv2.VideoCapture(selected_index)
        if not self.cap.isOpened():
            self.label.setText(f"Error: Could not open {selected_text}.")
            self.cap = None
            return

        original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if original_width == 0 or original_height == 0:
            print("Warning: Could not get valid camera resolution. Defaulting to 640x480.")
            self.original_frame_width = 640
            self.original_frame_height = 480
        else:
            self.original_frame_width = original_width
            self.original_frame_height = original_height
        self.aspect_ratio = self.original_frame_width / self.original_frame_height

        self.label.clear()
        self.is_camera_active = True
        self.start_stop_button.setText("Stop Camera")
        
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
        print(f"{selected_text} started.")
        self.update_frame()

    def stop_camera(self):
        if not self.is_camera_active: return
        
        if self.timer and self.timer.isActive():
            self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        self.is_camera_active = False
        self.start_stop_button.setText("Start Camera")
        self.label.clear()
        self.label.setText("Camera is stopped.")
        self.label.setStyleSheet("color: #abb2bf; font-weight: normal; font-size: 14px;")
        print("Camera stopped.")

    @smart_inference_mode()
    def update_frame(self):
        if not self.is_camera_active or self.cap is None or not self.cap.isOpened():
            self.label.setText("No active camera stream.")
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Warning: Failed to read frame from camera. Stopping camera.")
            self.stop_camera()
            return
        
        display_frame = frame.copy()
        
        annotator = Annotator(display_frame, line_width=2, example=str(self.names if self.yolo_loaded else [])) # Example for Annotator
        font = cv2.FONT_HERSHEY_SIMPLEX

        red_centers, green_centers = [], []
        new_degree = 0

        if self.yolo_loaded:
            img_for_detection = cv2.resize(frame, (640, 640))
            img_for_detection_rgb = cv2.cvtColor(img_for_detection, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_for_detection_rgb).to(self.device).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)
            
            with torch.no_grad():
                pred = self.model(img_tensor, augment=False, visualize=False)
                pred = non_max_suppression(pred, conf_thres=0.4, iou_thres=0.45)
            
            for det in pred:
                if len(det):
                    det[:, :4] = scale_boxes(img_tensor.shape[2:], det[:, :4], display_frame.shape).round()
                    for *xyxy, conf, cls in det:
                        class_name = self.names[int(cls)]
                        x1, y1, x2, y2 = map(int, xyxy)
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                        color = (255, 255, 255)
                        if "Red_Ball" in class_name:
                            red_centers.append((cx, cy))
                            color = (0, 0, 255)
                        elif "Green_Ball" in class_name:
                            green_centers.append((cx, cy))
                            color = (0, 255, 0)
                        
                        annotator.box_label(xyxy, f"{class_name} {conf:.2f}", color=colors(int(cls), True))
                        cv2.circle(display_frame, (cx, cy), 5, (255, 255, 255), -1)

            red_centers.sort(key=lambda pt: -pt[1])
            green_centers.sort(key=lambda pt: -pt[1])
            midpoint = None
            
            if red_centers and green_centers:
                red_nearest = red_centers[0]
                green_nearest = green_centers[0]
                
                midpoint = ((red_nearest[0] + green_nearest[0]) // 2, (red_nearest[1] + green_nearest[1]) // 2)
                cv2.line(display_frame, red_nearest, green_nearest, (200, 200, 200), 2)
                cv2.circle(display_frame, midpoint, 6, (255, 0, 255), -1)
                cv2.putText(display_frame, "Midpoint", (midpoint[0] - 40, midpoint[1] - 10), font, 0.6, (255, 0, 255), 2)

                bar_y = display_frame.shape[0] - 50
                bar_left = 50
                bar_right = display_frame.shape[1] - 50
                bar_width = bar_right - bar_left
                
                cv2.rectangle(display_frame, (bar_left, bar_y), (bar_right, bar_y + 20), (0, 140, 255), 2)
                center_x = (bar_left + bar_right) // 2
                cv2.line(display_frame, (center_x, bar_y), (center_x, bar_y + 20), (0, 140, 255), 2)
                
                cv2.putText(display_frame, "0", (bar_left - 10, bar_y + 40), font, 0.5, (255, 255, 255), 2)
                cv2.putText(display_frame, "90", (center_x - 15, bar_y + 40), font, 0.5, (255, 255, 255), 2)
                cv2.putText(display_frame, "180", (bar_right - 20, bar_y + 40), font, 0.5, (255, 255, 255), 2)

                if midpoint:
                    relative_position_on_bar = (midpoint[0] - bar_left) / bar_width
                    relative_position_on_bar = np.clip(relative_position_on_bar, 0, 1)

                    new_degree = int(relative_position_on_bar * 180)
                    
                    indicator_x = int(bar_left + relative_position_on_bar * bar_width - 15)
                    cv2.rectangle(display_frame, (indicator_x, bar_y), (indicator_x + 30, bar_y + 20), (0, 0, 255), -1)

                    text = f"{new_degree}°"
                    text_size = cv2.getTextSize(text, font, 0.6, 2)[0]
                    text_x = indicator_x + (30 - text_size[0]) // 2
                    text_y = bar_y - 10
                    cv2.putText(display_frame, text, (text_x, text_y), font, 0.6, (0, 0, 255), 2)
                    
                    if new_degree != self.current_degree:
                        self.current_degree = new_degree
                        self.degree_changed.emit(self.current_degree)
        
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = display_frame_rgb.shape
        q_image = QImage(display_frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        label_size = self.label.size()
        if label_size.width() > 0 and label_size.height() > 0:
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        else:
            self.label.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_camera_active:
            self.update_frame()

    def closeEvent(self, event):
        self.stop_camera()