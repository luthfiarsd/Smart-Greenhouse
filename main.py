"""
Simulasi Sistem IoT Smart Greenhouse:
Pemantauan Iklim Mikro (Suhu, Kelembapan, Cahaya) dan Sistem Deteksi Hama Berbasis ESP32 Terintegrasi Cloud
"""

import machine
import time
import dht
from machine import Pin, I2C
import ssd1306
import boot

# ========== KONFIGURASI HARDWARE ==========
DHT_PIN = 5
dht_sensor = dht.DHT11(Pin(DHT_PIN))

PIR_PIN = 4
pir_sensor = Pin(PIR_PIN, Pin.IN)

I2C_SDA = 19
I2C_SCL = 18
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

led = Pin(2, Pin.OUT)

BUZZER_PIN = 21
buzzer = Pin(BUZZER_PIN, Pin.OUT)

# ========== PARAMETER GREENHOUSE ==========
TEMP_MIN = 20  # Celsius
TEMP_MAX = 30  # Celsius
HUMID_MIN = 60  # Persen
HUMID_MAX = 80  # Persen

# ========== VARIABEL GLOBAL ==========
current_temp = 0
current_humid = 0
pest_detected = False
anomaly_status = ""
last_mqtt_publish = 0
MQTT_INTERVAL = 5000  # Interval publish 5 detik
dht_error_count = 0
MAX_DHT_ERRORS = 3

last_mqtt_check = 0
MQTT_CHECK_INTERVAL = 30000

last_led_toggle = 0
LED_BLINK_INTERVAL = 200  # Lebih cepat berkedip

last_buzzer_toggle = 0
BUZZER_BEEP_INTERVAL = 200  # Lebih cepat beep
BUZZER_BEEP_DURATION = 100


def read_dht_sensor():
    global current_temp, current_humid, dht_error_count

    for attempt in range(3):
        try:
            dht_sensor.measure()
            current_temp = dht_sensor.temperature()
            current_humid = dht_sensor.humidity()
            dht_error_count = 0
            print(f"DHT11 - Suhu: {current_temp}°C, Kelembapan: {current_humid}%")
            return True
        except OSError as e:
            if attempt < 2:
                time.sleep(0.5)
            dht_error_count += 1

    print(f"Error membaca DHT11 setelah 3 percobaan (Total errors: {dht_error_count})")
    return False


# ========== FUNGSI SISTEM PIR SENSOR ==========
def read_pir_sensor():
    global pest_detected
    pest_detected = pir_sensor.value() == 1
    if pest_detected:
        print("PIR: Gerakan terdeteksi! (Potensi Hama)")
    return pest_detected


# ========== ANALISIS KONDISI GREENHOUSE ==========
def analyze_greenhouse_condition():
    global anomaly_status

    # Deteksi hama
    if pest_detected:
        anomaly_status = "HAMA TERDETEKSI!"
        return anomaly_status

    # Analisis Suhu
    if current_temp > TEMP_MAX:
        temp_status = "SUHU TINGGI"
    elif current_temp < TEMP_MIN:
        temp_status = "SUHU RENDAH"
    else:
        temp_status = "SUHU OK"

    # Analisis Kelembapan
    if current_humid > HUMID_MAX:
        humid_status = "LEMBAB TINGGI"
    elif current_humid < HUMID_MIN:
        humid_status = "LEMBAB RENDAH"
    else:
        humid_status = "LEMBAB OK"

    # Kombinasi Status
    if temp_status == "SUHU OK" and humid_status == "LEMBAB OK":
        anomaly_status = "OPTIMAL"
    elif temp_status != "SUHU OK" and humid_status != "LEMBAB OK":
        anomaly_status = f"{temp_status}\n{humid_status}"
    elif temp_status != "SUHU OK":
        anomaly_status = temp_status
    else:
        anomaly_status = humid_status

    return anomaly_status


# ========== FUNGSI SISTEM OLED DISPLAY ==========
def display_normal_status():
    oled.fill(0)
    oled.text("SMART GREENHOUSE", 0, 0)
    oled.text("-" * 16, 0, 10)
    oled.text(f"Suhu: {current_temp}C", 0, 20)
    oled.text(f"Lembab: {current_humid}%", 0, 30)
    oled.text(f"PIR: {'AKTIF' if pest_detected else 'AMAN'}", 0, 40)
    oled.text("Status: OK", 0, 50)
    oled.show()


def display_anomaly_alert():
    oled.fill(0)

    oled.fill_rect(0, 0, 128, 12, 1)
    oled.text("!!! ANOMALI !!!", 5, 2, 0)

    oled.text("-" * 16, 0, 15)
    oled.text(f"T:{current_temp}C H:{current_humid}%", 0, 25)

    lines = anomaly_status.split("\n")
    y_pos = 35
    for line in lines[:2]:
        oled.text(line[:16], 0, y_pos)
        y_pos += 10

    if pest_detected:
        oled.fill_rect(0, 54, 128, 10, 1)
        oled.text("HAMA DETECTED!", 10, 55, 0)

    oled.show()


def update_display():
    if anomaly_status == "OPTIMAL":
        display_normal_status()
    else:
        display_anomaly_alert()


# ========== FUNGSI MQTT CONNECTION MANAGEMENT ==========
def check_and_reconnect_mqtt():
    global last_mqtt_check

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_mqtt_check) >= MQTT_CHECK_INTERVAL:
        last_mqtt_check = current_time

        try:
            if boot.mqtt_client:
                boot.mqtt_client.ping()
            else:
                print("MQTT disconnected, attempting reconnect...")
                boot.connect_mqtt()
        except Exception as e:
            print(f"MQTT connection check failed: {e}, reconnecting...")
            try:
                boot.connect_mqtt()
            except Exception as e2:
                print(f"Reconnection failed: {e2}")


# ========== FUNGSI MQTT PUBLISHING ==========
def publish_to_cloud():
    global last_mqtt_publish

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_mqtt_publish) >= MQTT_INTERVAL:
        try:
            if not boot.mqtt_client:
                print("MQTT client belum terhubung, mencoba reconnect...")
                boot.connect_mqtt()
                return

            # Format: {"variable_name": {"value": number}, ...}
            payload = {
                "temperature": current_temp,
                "humidity": current_humid,
                "pest_detected": 1 if pest_detected else 0,  # 1 = detected, 0 = clear
                "status": (
                    1 if anomaly_status == "OPTIMAL" else 0
                ),  # 1 = optimal, 0 = anomali
            }

            boot.publish_data(payload)

            last_mqtt_publish = current_time
            print(f"Data published to Ubidots - Status: {anomaly_status}")

        except Exception as e:
            print(f"Error publishing to MQTT: {e}")
            boot.mqtt_client = None


# ========== FUNGSI LED INDIKATOR ==========
def update_led_indicator():
    global last_led_toggle
    if pest_detected or anomaly_status != "OPTIMAL":
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_led_toggle) >= LED_BLINK_INTERVAL:
            led.value(not led.value())
            last_led_toggle = current_time
    else:
        led.value(0)


# ========== FUNGSI BUZZER INDIKATOR ==========
buzzer_state = 0


def update_buzzer_indicator():
    global last_buzzer_toggle, buzzer_state

    if pest_detected or anomaly_status != "OPTIMAL":
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_buzzer_toggle) >= BUZZER_BEEP_INTERVAL:
            buzzer_state = not buzzer_state
            buzzer.value(buzzer_state)
            last_buzzer_toggle = current_time
    else:
        buzzer.value(0)
        buzzer_state = 0


# ========== MAIN LOOP ==========
def main():
    print("\n" + "=" * 40)
    print("SISTEM SMART GREENHOUSE AKTIF")
    print("Monitoring: Suhu, Kelembapan, Deteksi Hama")
    print("=" * 40 + "\n")

    # Tampilan awal
    oled.fill(0)
    oled.text("SMART GREENHOUSE", 0, 0)
    oled.text("Initializing...", 0, 30)
    oled.show()

    # Connect to WiFi and MQTT
    print("Menghubungkan ke WiFi...")
    if boot.connect_wifi():
        time.sleep(2)
        print("Menghubungkan ke MQTT...")
        boot.connect_mqtt()
    else:
        print("WARNING: WiFi connection failed, running in offline mode")

    time.sleep(1)

    loop_count = 0

    last_dht_read = 0
    DHT_READ_INTERVAL = 2000  # Baca DHT setiap 2 detik
    last_display_update = 0
    DISPLAY_UPDATE_INTERVAL = 500  # Update display setiap 500ms

    while True:
        try:
            current_time = time.ticks_ms()

            # 1. Baca sensor PIR terus menerus (prioritas tinggi, tanpa delay)
            read_pir_sensor()

            # 2. Update LED & Buzzer indikator setiap loop (tanpa delay)
            update_led_indicator()
            update_buzzer_indicator()

            # 3. Baca sensor DHT11 dengan interval (hemat resource)
            if time.ticks_diff(current_time, last_dht_read) >= DHT_READ_INTERVAL:
                dht_success = read_dht_sensor()
                last_dht_read = current_time

                if not dht_success and dht_error_count > MAX_DHT_ERRORS:
                    print("DHT11 error threshold exceeded, skipping DHT read...")

            # 4. Analisis kondisi greenhouse
            status = analyze_greenhouse_condition()

            # 5. Update OLED Display dengan interval
            if (
                time.ticks_diff(current_time, last_display_update)
                >= DISPLAY_UPDATE_INTERVAL
            ):
                update_display()
                last_display_update = current_time

            # 6. Check and maintain MQTT connection
            check_and_reconnect_mqtt()

            # 7. Publish data ke cloud MQTT
            publish_to_cloud()

            # Log setiap 10 loop
            loop_count += 1
            if loop_count % 50 == 0:  # Kurangi frekuensi log
                print(f"\n[Loop #{loop_count}] Status Greenhouse: {status}")
                print(
                    f"Suhu: {current_temp}°C | Kelembapan: {current_humid}% | Hama: {'YA' if pest_detected else 'TIDAK'}\n"
                )

            # Delay minimal agar loop tetap responsif
            time.sleep_ms(50)  # 50ms delay, sangat responsif

        except KeyboardInterrupt:
            print("\n\nSistem dihentikan oleh user")
            oled.fill(0)
            oled.text("System Stopped", 10, 28)
            oled.show()

            try:
                if boot.mqtt_client:
                    boot.mqtt_client.disconnect()
            except:
                pass
            break

        except Exception as e:
            print(f"Error di main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
