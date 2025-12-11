import network
import time
from umqtt.simple import MQTTClient
import machine
import urequests

WIFI_SSID = "KOST RAYA 2"
WIFI_PASSWORD = "cikuda03"

MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883
MQTT_USER = "BBUS-ATew3sfvzU8mpzpKw4zGSYJLtmCoVC"
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_greenhouse"

DEVICE_LABEL = "smart-greenhouse"

MQTT_TOPIC_PUBLISH = "/v1.6/devices/" + DEVICE_LABEL

GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyz9jjuty9m-EJvXZm6uM5s10SYLJJSNrYGww_NrSiZV1cDM0XwGEc5WYeYGtdE21_s/exec"

mqtt_client = None


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Menghubungkan ke WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        timeout = 0
        while not wlan.isconnected() and timeout < 10:
            time.sleep(1)
            timeout += 1
            print(".", end="")

        if wlan.isconnected():
            print("\nWiFi terhubung!")
            print("IP Address:", wlan.ifconfig()[0])
            return True
        else:
            print("\nGagal terhubung ke WiFi")
            return False
    else:
        print("WiFi sudah terhubung")
        print("IP Address:", wlan.ifconfig()[0])
        return True


def connect_mqtt():
    global mqtt_client
    try:
        mqtt_client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
        )
        mqtt_client.connect()
        print("MQTT terhubung ke Ubidots:", MQTT_BROKER)
        return True
    except Exception as e:
        print("Gagal terhubung ke MQTT:", e)
        return False


def publish_data(payload_dict):
    """payload_dict: format {"variable_label_name": value}"""
    global mqtt_client
    try:
        if mqtt_client:
            import ujson

            payload = ujson.dumps(payload_dict)
            mqtt_client.publish(MQTT_TOPIC_PUBLISH, payload)
            return True
    except Exception as e:
        print("Error publish MQTT:", e)
        try:
            connect_mqtt()
        except:
            pass
    return False


def send_to_google_sheets(data_dict):
    """
    Mengirim data ke Google Sheets via Apps Script webhook
    data_dict: {"temperature": 25, "humidity": 70, "pest_detected": 0, "status": "OPTIMAL"}
    """
    try:
        # Google Apps Script biasanya menerima data sebagai query parameters
        # Encode URL untuk menghindari error dengan karakter khusus

        def url_encode(s):
            """Simple URL encoding untuk MicroPython"""
            s = str(s)
            s = s.replace(" ", "%20")
            s = s.replace("\n", "%0A")
            s = s.replace("!", "%21")
            return s

        # Konversi data_dict ke query string
        params = []
        for key, value in data_dict.items():
            encoded_value = url_encode(value)
            params.append(f"{key}={encoded_value}")

        query_string = "&".join(params)
        url_with_params = f"{GOOGLE_APPS_SCRIPT_URL}?{query_string}"

        print(f"Sending to Google Sheets...")

        # Gunakan GET request (lebih kompatibel dengan Google Apps Script)
        response = urequests.get(url_with_params)

        # print(f"Google Sheets Response: {response.status_code}")

        # # Ambil response text hanya jika ada
        # try:
        #     resp_text = response.text
        #     if len(resp_text) < 200:  # Hanya print jika tidak terlalu panjang
        #         print(f"Response: {resp_text}")
        # except:
        #     pass

        response.close()

        if response.status_code == 200 or response.status_code == 302:
            print("✓ Data berhasil dikirim ke Google Sheets")
            return True
        # else:
        #     # print(f"✗ Gagal mengirim ke Google Sheets: {response.status_code}")
        #     return False

    except Exception as e:
        print(f"Error sending to Google Sheets: {e}")
        return False


# Inisialisasi koneksi saat boot
print("=" * 40)
print("SMART GREENHOUSE SYSTEM")
print("=" * 40)

if connect_wifi():
    time.sleep(2)
    connect_mqtt()
else:
    print("Sistem berjalan tanpa koneksi internet")

print("Boot selesai, menjalankan main.py...")
