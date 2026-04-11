"""
Light Sensor Simulator
──────────────────────
Simulates a BH1750 ambient light sensor.
Publishes to:  parking/{lot_id}/environment/light
"""

import json
import time
import math
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, LOT_ID, LIGHT_INTERVAL


def get_simulated_light() -> tuple:
    """Return (lux, is_daylight) following a day/night cycle."""
    hour = datetime.now().hour + datetime.now().minute / 60.0

    if 6 <= hour <= 18:
        # Daytime: sinusoidal curve peaking at noon
        base_lux = 800 * math.sin(math.pi * (hour - 6) / 12)
        # Simulate cloud cover
        cloud_factor = random.choice([1.0, 1.0, 1.0, 0.6, 0.4])
        lux = base_lux * cloud_factor + random.uniform(-30, 30)
    else:
        # Night time: dim artificial lighting
        lux = random.uniform(5, 50)

    lux = max(0, round(lux, 1))
    is_daylight = lux > 500

    return lux, is_daylight


def run():
    client = mqtt.Client(client_id="light-sim", protocol=mqtt.MQTTv311)
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    print(f"[Light] Publishing every {LIGHT_INTERVAL}s")

    try:
        while True:
            lux, daylight = get_simulated_light()
            payload = {
                "lot_id": LOT_ID,
                "lux": lux,
                "daylight": daylight,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            topic = f"parking/{LOT_ID}/environment/light"
            client.publish(topic, json.dumps(payload), qos=0)
            icon = "☀️" if daylight else "🌙"
            print(f"  {icon}  {lux} lux")
            time.sleep(LIGHT_INTERVAL)
    except KeyboardInterrupt:
        print("[Light] Shutting down …")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
