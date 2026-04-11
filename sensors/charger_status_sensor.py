"""
Charger Status Sensor (Mock)
────────────────────────────
Simulates EV charger state machines.
Publishes to:  parking/{lot_id}/charger/{charger_id}/status
"""

import json
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, LOT_ID, TOTAL_CHARGERS, CHARGER_STATUS_INTERVAL


# ─── State Machine ──────────────────────────────────────────────
TRANSITIONS = {
    "available":  [("in_use", 0.15), ("offline", 0.02)],
    "in_use":     [("available", 0.05), ("blocked", 0.08), ("faulted", 0.03)],
    "blocked":    [("available", 0.10)],
    "faulted":    [("available", 0.08)],
    "offline":    [("available", 0.12)],
}


class ChargerStatusSensor:
    def __init__(self, charger_id: str):
        self.charger_id = charger_id
        self.status = "available"
        self.vehicle_id = None

    def tick(self) -> dict:
        """Advance one time-step and maybe transition state."""
        for next_state, prob in TRANSITIONS.get(self.status, []):
            if random.random() < prob:
                self.status = next_state
                if self.status == "in_use":
                    self.vehicle_id = f"EV-{random.randint(1000, 9999)}"
                elif self.status in ("available", "offline"):
                    self.vehicle_id = None
                break

        return {
            "charger_id": self.charger_id,
            "lot_id": LOT_ID,
            "status": self.status,
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def run():
    client = mqtt.Client(client_id="charger-status-sim", protocol=mqtt.MQTTv311)
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    chargers = [ChargerStatusSensor(f"CHG-{i:02d}") for i in range(1, TOTAL_CHARGERS + 1)]
    print(f"[ChargerStatus] Simulating {len(chargers)} chargers  →  "
          f"publishing every {CHARGER_STATUS_INTERVAL}s")

    try:
        while True:
            for ch in chargers:
                reading = ch.tick()
                topic = f"parking/{LOT_ID}/charger/{ch.charger_id}/status"
                client.publish(topic, json.dumps(reading), qos=0)
            time.sleep(CHARGER_STATUS_INTERVAL)
    except KeyboardInterrupt:
        print("[ChargerStatus] Shutting down …")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
