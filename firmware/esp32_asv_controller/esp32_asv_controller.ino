// Import library yang diperlukan
#include <ESP32Servo.h>

// --- Konfigurasi Pin ---
const int SERVO_PIN = 13;
const int MOTOR_PIN = 12;

// Buat objek untuk Servo dan Motor
Servo servoKemudi;
Servo motorESC;

// --- Variabel untuk Pengiriman Telemetri ---
unsigned long lastTelemetryTime = 0;     // Menyimpan waktu terakhir telemetri dikirim
const long telemetryInterval = 1000;     // Interval pengiriman telemetri (1000 ms = 1 detik)

void setup() {
  Serial.begin(115200); 
  
  servoKemudi.attach(SERVO_PIN, 500, 2500);
  motorESC.attach(MOTOR_PIN, 1000, 2000);

  servoKemudi.write(90);
  motorESC.writeMicroseconds(1500);
  delay(2000); 

  Serial.println("ESP32 Siap Menerima Perintah...");
}

void loop() {
  // Cek apakah ada perintah masuk dari GUI
  if (Serial.available() > 0) {
    processSerialCommand(); // Proses perintah yang masuk
  }

  // Cek apakah sudah waktunya mengirim data telemetri
  unsigned long currentTime = millis();
  if (currentTime - lastTelemetryTime >= telemetryInterval) {
    lastTelemetryTime = currentTime; // Reset waktu terakhir
    sendTelemetry(); // Kirim data telemetri
  }
}

void processSerialCommand() {
  // Fungsi ini sama seperti sebelumnya, untuk memproses perintah seperti S1550;D90
  String dataMasuk = Serial.readStringUntil('\n');
  dataMasuk.trim();
  
  int s_pos = dataMasuk.indexOf('S');
  int d_pos = dataMasuk.indexOf('D');
  int semicolon_pos = dataMasuk.indexOf(';');

  if (s_pos != -1 && d_pos != -1 && semicolon_pos != -1) {
    String speedString = dataMasuk.substring(s_pos + 1, semicolon_pos);
    int speedValue = speedString.toInt();

    String degreeString = dataMasuk.substring(d_pos + 1);
    int degreeValue = degreeString.toInt();

    speedValue = constrain(speedValue, 1500, 2000);
    degreeValue = constrain(degreeValue, 0, 180);

    motorESC.writeMicroseconds(speedValue);
    servoKemudi.write(degreeValue);
  }
}

void sendTelemetry() {
  // === FUNGSI BARU UNTUK MENGIRIM DATA SENSOR ===
  // Di sini kita menggunakan data acak sebagai simulasi.
  // Ganti bagian ini dengan pembacaan sensor Anda yang sebenarnya.
  
  // Simulasi data GPS di sekitar Tanjung Pinang
  float lat = -6.2088 + (random(-50, 50) / 10000.0);
  float lon = 106.8456 + (random(-50, 50) / 10000.0);
  int sats = random(8, 15);

  // Simulasi data Baterai
  float battery = 11.5 + (random(0, 13) / 10.0);

  // Simulasi data Kompas
  int compass = random(0, 360);

  // Simulasi data Kecepatan
  float speed = 1.5 + (random(0, 20) / 10.0);

  // Buat string telemetri dengan format yang telah ditentukan
  String telemetryData = "T:";
  telemetryData += "GPS," + String(lat, 4) + "," + String(lon, 4) + "," + String(sats) + ";";
  telemetryData += "BAT," + String(battery, 1) + ";";
  telemetryData += "COMP," + String(compass) + ";";
  telemetryData += "SPD," + String(speed, 1);

  // Kirim string telemetri ke aplikasi Python
  Serial.println(telemetryData);
}
