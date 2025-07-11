# core/pid_controller.py

import time

class PIDController:
    """
    Kelas sederhana untuk implementasi kontroler PID.
    """
    def __init__(self, Kp, Ki, Kd, setpoint):
        """
        Inisialisasi kontroler PID.

        Args:
            Kp (float): Gain Proportional
            Ki (float): Gain Integral
            Kd (float): Gain Derivative
            setpoint (float): Nilai target yang ingin dicapai.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        
        # Inisialisasi variabel internal
        self.last_error = 0
        self.integral = 0
        self.last_time = time.time()

    def update(self, current_value):
        """
        Menghitung output koreksi berdasarkan nilai saat ini.

        Args:
            current_value (float): Nilai yang diukur saat ini (misal: derajat dari kamera).

        Returns:
            float: Nilai output koreksi yang harus diterapkan.
        """
        current_time = time.time()
        dt = current_time - self.last_time # Delta time, selisih waktu dari update terakhir

        if dt == 0:
            return 0 # Hindari pembagian dengan nol

        # Hitung error
        error = self.setpoint - current_value
        
        # Hitung komponen Integral (akumulasi error dari waktu ke waktu)
        self.integral += error * dt
        
        # Hitung komponen Derivative (laju perubahan error)
        derivative = (error - self.last_error) / dt
        
        # Hitung output PID
        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)
        
        # Simpan nilai saat ini untuk perhitungan berikutnya
        self.last_error = error
        self.last_time = current_time
        
        return output

    def reset(self):
        """Mereset state kontroler."""
        self.last_error = 0
        self.integral = 0
        self.last_time = time.time()
