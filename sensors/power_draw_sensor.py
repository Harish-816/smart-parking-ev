"""
Power Draw Sensor (Mock)
────────────────────────
Simulates EV charging power curves.
Publishes to:  parking/{lot_id}/charger/{charger_id}/power
"""

import json
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, LOT_ID,
    TOTAL_CHARGERS, POWER_DRAW_INTERVAL, MAX_POWER_KW
)
from sqs_publisher import send_to_sqs, is_sqs_enabled


class PowerDrawSensor:
    def __init__(self, charger_id: str):
        self.charger_id = charger_id
        self.power_kw = 0.0
        self.energy_kwh = 0.0
        self.charging = False
        self.session_tick = 0
        self.session_length = 0

    def start_session(self):
        self.charging = True
        self.session_tick = 0
        self.session_length = random.randint(60, 300)
        self.energy_kwh = 0.0

    def stop_session(self):
        self.charging = False
        self.power_kw = 0.0
        self.session_tick = 0

    def tick(self) -> dict:
        if self.charging:
            progress = self.session_tick / max(self.session_length, 1)
            if progress < 0.1:
                self.power_kw = MAX_POWER_KW * (progress / 0.1) + random.uniform(-0.3, 0.3)
            elif progress < 0.75:
                self.power_kw = MAX_POWER_KW + random.uniform(-0.5, 0.5)
            elif progress < 0.95:
                taper = 1 - ((progress - 0.75) / 0.20)
                self.power_kw = MAX_POWER_KW * taper + random.uniform(-0.3, 0.3)
            else:
                self.power_kw = random.uniform(0.0, 0.3)

            self.power_kw = max(0.0, self.power_kw)
            self.energy_kwh += self.power_kw * (POWER_DRAW_INTERVAL / 3600)
            self.session_tick += 1

            if self.session_tick >= self.session_length:
                self.stop_session()
        else:
            self.power_kw = 0.0
            if random.random() < 0.05:
                self.start_session()

        return {
            "charger_id": self.charger_id,
            "lot_id": LOT_ID,
            "power_kw": round(self.power_kw, 2),
            "energy_kwh": round(self.energy_kwh, 3),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def run():
    client = mqtt.Client(client_id="power-draw-sensor", protocol=mqtt.MQTTv311)
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    sensors = [PowerDrawSensor(f"CHG-{i:02d}") for i in range(1, TOTAL_CHARGERS + 1)]
    print(f"[PowerDraw] Simulating {len(sensors)} chargers  →  "
          f"publishing every {POWER_DRAW_INTERVAL}s to MQTT")

    try:
        while True:
            for s in sensors:
                reading = s.tick()
                topic = f"parking/{LOT_ID}/charger/{s.charger_id}/power"
                client.publish(topic, json.dumps(reading))
                # Dual-publish to SQS when running on AWS
                if is_sqs_enabled():
                    send_to_sqs(topic, reading)
            time.sleep(POWER_DRAW_INTERVAL)
    except KeyboardInterrupt:
        print("[PowerDraw] Shutting down …")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
