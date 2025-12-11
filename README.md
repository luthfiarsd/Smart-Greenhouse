# Smart Greenhouse IoT System

Sistem IoT berbasis ESP32 untuk pemantauan iklim mikro dan deteksi hama pada greenhouse secara real-time dengan integrasi cloud.

## Fitur Utama

- **Monitoring Suhu & Kelembapan** menggunakan sensor DHT11
- **Deteksi Hama** menggunakan sensor PIR
- **Display OLED** untuk visualisasi data secara langsung
- **Notifikasi LED & Buzzer** untuk alert anomali
- **Cloud Integration** ke Ubidots (MQTT) dan Google Sheets
- **Auto-reconnect** WiFi dan MQTT

## Hardware

- ESP32 Microcontroller
- Sensor DHT11 (Suhu & Kelembapan)
- Sensor PIR (Deteksi Gerakan)
- OLED Display 128x64 (I2C)
- LED Indikator
- Buzzer
- Kabel Jumper & Breadboard

## Pin Configuration

| Komponen   | Pin ESP32 |
| ---------- | --------- |
| DHT11      | GPIO 5    |
| PIR Sensor | GPIO 4    |
| OLED SDA   | GPIO 19   |
| OLED SCL   | GPIO 18   |
| LED        | GPIO 2    |
| Buzzer     | GPIO 21   |

## Parameter Optimal Greenhouse

- **Suhu**: 20-30°C
- **Kelembapan**: 60-80%

## Cloud Services

1. **Ubidots** - Real-time monitoring dan dashboard
2. **Google Sheets** - Data logging dan pencatatan historis

## File Structure

```
Smart-Greenhouse/
├── boot.py          # Konfigurasi WiFi dan MQTT
├── main.py          # Program utama sistem
└── lib/
    ├── ssd1306.py   # Library OLED display
    └── umqtt/
        └── simple.py # Library MQTT
```

## Status Sistem

Sistem mendeteksi berbagai kondisi:

- `OPTIMAL` - Semua parameter normal
- `SUHU TINGGI/RENDAH` - Suhu di luar range
- `LEMBAB TINGGI/RENDAH` - Kelembapan di luar range
- `HAMA TERDETEKSI!` - Gerakan terdeteksi oleh PIR
