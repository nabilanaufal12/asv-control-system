# core/serial_handler.py

import serial
import serial.tools.list_ports
import time
# Impor QThread dan pyqtSignal untuk membuat proses 'mendengarkan' di latar belakang
from PyQt5.QtCore import QThread, pyqtSignal

# === KELAS BARU: Thread untuk Membaca Data Serial ===
class SerialReader(QThread):
    """
    Kelas ini berjalan di thread terpisah. Tujuannya adalah untuk terus-menerus
    mendengarkan data yang masuk dari port serial tanpa membuat antarmuka (GUI) utama menjadi beku.
    """
    # Definisikan sinyal yang akan dipancarkan saat ada data baru yang diterima.
    # Sinyal ini membawa satu argumen string (data yang dibaca).
    data_received = pyqtSignal(str)

    def __init__(self, serial_instance):
        """Konstruktor, menerima instance koneksi serial yang aktif."""
        super().__init__()
        self.ser = serial_instance
        self.running = True # Flag untuk mengontrol apakah loop harus terus berjalan.

    def run(self):
        """
        Metode ini akan dieksekusi secara otomatis saat thread dimulai (dengan .start()).
        Ini adalah inti dari proses 'mendengarkan'.
        """
        print("Serial reader thread dimulai...")
        while self.running and self.ser and self.ser.is_open:
            try:
                # Cek apakah ada byte yang menunggu untuk dibaca di buffer serial.
                if self.ser.in_waiting > 0:
                    # Baca satu baris data (diakhiri dengan karakter newline '\n').
                    line = self.ser.readline()
                    # Decode dari format bytes ke string, abaikan error jika ada karakter aneh.
                    # .strip() menghapus spasi atau karakter tak terlihat di awal/akhir.
                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        # Jika teks tidak kosong, pancarkan sinyal dengan data tersebut.
                        self.data_received.emit(text)
            except serial.SerialException:
                # Jika terjadi error (misal: perangkat dicabut), hentikan loop.
                print("Error port serial. Menghentikan thread pembaca.")
                break
        print("Serial reader thread selesai.")

    def stop(self):
        """Metode untuk menghentikan loop pembacaan dari luar thread."""
        self.running = False


class SerialHandler:
    """
    Kelas ini mengelola semua aspek komunikasi serial dengan perangkat keras (ESP32),
    termasuk mengirim dan menerima data.
    """
    def __init__(self):
        self.ser = None # Menyimpan objek koneksi serial
        self.reader_thread = None # Menyimpan objek thread pembaca

    def list_available_ports(self):
        """Mendeteksi semua COM port yang tersedia di sistem."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port, baud_rate=115200):
        """Mencoba membuka koneksi serial dan memulai thread pembaca."""
        try:
            if self.ser and self.ser.is_open:
                self.disconnect() # Putuskan koneksi lama jika ada
                
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(2) # Beri waktu agar koneksi stabil
            
            if self.ser.is_open:
                print(f"Berhasil terhubung ke {port}.")
                # === PERUBAHAN: Mulai thread pembaca setelah terhubung ===
                self.reader_thread = SerialReader(self.ser)
                self.reader_thread.start() # Jalankan thread di latar belakang
                return True
            return False
        except serial.SerialException as e:
            print(f"Error saat menghubungkan ke {port}: {e}")
            self.ser = None
            return False

    def disconnect(self):
        """Menghentikan thread pembaca dan menutup koneksi serial."""
        # === PERUBAHAN: Hentikan thread pembaca sebelum menutup koneksi ===
        if self.reader_thread:
            self.reader_thread.stop() # Set flag 'running' menjadi False
            self.reader_thread.wait() # Tunggu thread benar-benar berhenti
            self.reader_thread = None

        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Koneksi serial ditutup.")
        self.ser = None

    def send_data(self, data):
        """Mengirim data string ke perangkat yang terhubung."""
        if self.is_connected():
            try:
                # Kirim data sebagai bytes dengan encoding utf-8.
                self.ser.write(data.encode('utf-8'))
                return True
            except serial.SerialException as e:
                print(f"Error saat menulis ke port serial: {e}")
                self.disconnect() # Putuskan koneksi jika ada error
                return False
        return False

    def is_connected(self):
        """Mengecek apakah koneksi serial sedang aktif."""
        return self.ser is not None and self.ser.is_open
