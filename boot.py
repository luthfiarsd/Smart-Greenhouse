import network
import time
from umqtt.simple import MQTTClient
import machine

WIFI_SSID = "KOST RAYA 2"
WIFI_PASSWORD = "cikuda03"

MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883
MQTT_USER = "BBUS-ATew3sfvzU8mpzpKw4zGSYJLtmCoVC"
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_greenhouse"

DEVICE_LABEL = "smart-greenhouse"

MQTT_TOPIC_PUBLISH = "/v1.6/devices/" + DEVICE_LABEL

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