// Import library yang diperlukan
#include <ESP32Servo.h>

// --- Konfigurasi Pin ---
// Ganti angka pin ini sesuai dengan koneksi di kapal Anda
const int SERVO_PIN = 13; // Pin untuk sinyal servo kemudi
const int MOTOR_PIN = 12; // Pin untuk sinyal ESC (motor)

// Buat objek untuk Servo dan Motor
Servo servoKemudi;
Servo motorESC;

void setup() {
  // Mulai komunikasi serial dengan kecepatan (baud rate) yang sama dengan di Python nantinya
  Serial.begin(115200); 
  
  // Hubungkan objek servo dan motor ke pin yang telah ditentukan
  servoKemudi.attach(SERVO_PIN);
  motorESC.attach(MOTOR_PIN);

  // Inisialisasi posisi awal
  servoKemudi.write(90);      // Atur servo ke posisi tengah (90 derajat)
  motorESC.writeMicroseconds(1500); // Atur motor ke posisi netral/berhenti (1500 us)

  Serial.println("ESP32 Siap Menerima Perintah...");
}

void loop() {
  // Cek apakah ada data yang masuk dari port serial
  if (Serial.available() > 0) {
    // Baca data string yang masuk sampai bertemu karakter newline ('\n')
    String dataMasuk = Serial.readStringUntil('\n');
    
    // Tampilkan data yang diterima untuk debugging
    Serial.print("Data Diterima: ");
    Serial.println(dataMasuk);

    // Cari posisi pemisah 'S', ';', dan 'D'
    int s_pos = dataMasuk.indexOf('S');
    int d_pos = dataMasuk.indexOf('D');
    int semicolon_pos = dataMasuk.indexOf(';');

    // Pastikan format data benar sebelum diurai
    if (s_pos != -1 && d_pos != -1 && semicolon_pos != -1) {
      // Ekstrak nilai kecepatan (PWM) dari string
      String speedString = dataMasuk.substring(s_pos + 1, semicolon_pos);
      int speedValue = speedString.toInt();

      // Ekstrak nilai derajat servo dari string
      String degreeString = dataMasuk.substring(d_pos + 1);
      int degreeValue = degreeString.toInt();

      // Tampilkan hasil parsing untuk debugging
      Serial.print("Speed (PWM): ");
      Serial.print(speedValue);
      Serial.print(" | Degree: ");
      Serial.println(degreeValue);

      // --- Kontrol Hardware ---
      // Batasi nilai agar tetap dalam rentang aman
      speedValue = constrain(speedValue, 1500, 2000); // Batas aman untuk motor
      degreeValue = constrain(degreeValue, 0, 180);   // Batas aman untuk servo

      // Kirim perintah ke motor dan servo
      motorESC.writeMicroseconds(speedValue); // Gunakan writeMicroseconds untuk ESC
      servoKemudi.write(degreeValue);         // Gunakan write untuk servo
    } else {
      Serial.println("Format data salah!");
    }
  }
}
