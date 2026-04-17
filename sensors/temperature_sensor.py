"""
Temperature Sensor Simulator
─────────────────────────────
Simulates a DHT22 temperature + humidity sensor.
Publishes to:  parking/{lot_id}/environment/temperature
"""

import json
import time
import math
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, LOT_ID, TEMPERATURE_INTERVAL
from sqs_publisher import send_to_sqs, is_sqs_enabled


def get_simulated_temperature() -> tuple:
    """Return (temp_c, humidity_pct) following a daily cycle."""
    hour = datetime.now().hour + datetime.now().minute / 60.0
    base_temp = 25 + 8 * math.sin(math.pi * (hour - 6) / 12)
    temp_c = base_temp + random.uniform(-1.0, 1.0)

    humidity = 60 - 15 * math.sin(math.pi * (hour - 6) / 12) + random.uniform(-5, 5)
    humidity = max(20, min(95, humidity))

    return round(temp_c, 1), round(humidity, 1)


def run():
    client = mqtt.Client(client_id="temperature-sensor", protocol=mqtt.MQTTv311)
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    print(f"[Temperature] Publishing every {TEMPERATURE_INTERVAL}s to MQTT")

    try:
        while True:
            temp_c, humidity_pct = get_simulated_temperature()
            payload = {
                "lot_id": LOT_ID,
                "temp_c": temp_c,
                "humidity_pct": humidity_pct,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            topic = f"parking/{LOT_ID}/environment/temperature"
            client.publish(topic, json.dumps(payload))
            # Dual-publish to SQS when running on AWS
            if is_sqs_enabled():
                send_to_sqs(topic, payload)
            print(f"  🌡️  {temp_c}°C  |  💧 {humidity_pct}%")
            time.sleep(TEMPERATURE_INTERVAL)
    except KeyboardInterrupt:
        print("[Temperature] Shutting down …")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
