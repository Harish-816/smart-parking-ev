"""
Occupancy Sensor Simulator (Ultrasonic HC-SR04)
───────────────────────────────────────────────
Simulates ultrasonic distance sensors for each parking spot.
Publishes to:  parking/{lot_id}/spot/{spot_id}/occupancy
"""

import json
import time
import random
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, LOT_ID,
    TOTAL_SPOTS, OCCUPANCY_INTERVAL,
    OCCUPANCY_THRESHOLD_CM, OCCUPANCY_NOISE_PROB
)


class OccupancySensor:
    def __init__(self, spot_id: str, initially_occupied: bool = False):
        self.spot_id = spot_id
        self.occupied = initially_occupied

    def read(self) -> dict:
        """Simulate an ultrasonic distance reading."""
        # Small probability of a noisy/flipped reading
        is_noise = random.random() < OCCUPANCY_NOISE_PROB

        # Randomly change state occasionally (vehicle arrives / departs)
        if random.random() < 0.02:  # 2 % chance per reading
            self.occupied = not self.occupied

        effective_state = self.occupied if not is_noise else (not self.occupied)

        if effective_state:
            distance_cm = random.uniform(5, OCCUPANCY_THRESHOLD_CM - 5)
        else:
            distance_cm = random.uniform(OCCUPANCY_THRESHOLD_CM + 20, 300)

        return {
            "spot_id": self.spot_id,
            "lot_id": LOT_ID,
            "distance_cm": round(distance_cm, 1),
            "occupied": effective_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def run():
    client = mqtt.Client(client_id="occupancy-sensor-sim", protocol=mqtt.MQTTv311)
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    # Create sensors — ~60 % initially occupied
    sensors = []
    for i in range(1, TOTAL_SPOTS + 1):
        spot_id = f"SPOT-{i:03d}"
        sensors.append(OccupancySensor(spot_id, initially_occupied=random.random() < 0.6))

    print(f"[Occupancy] Simulating {len(sensors)} spots  →  "
          f"publishing every {OCCUPANCY_INTERVAL}s")

    try:
        while True:
            for sensor in sensors:
                reading = sensor.read()
                topic = f"parking/{LOT_ID}/spot/{sensor.spot_id}/occupancy"
                client.publish(topic, json.dumps(reading), qos=0)
            time.sleep(OCCUPANCY_INTERVAL)
    except KeyboardInterrupt:
        print("[Occupancy] Shutting down …")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
