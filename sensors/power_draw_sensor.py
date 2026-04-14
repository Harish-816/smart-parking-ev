"""
Power Draw Sensor (Mock)
────────────────────────
Simulates EV charging power curves.
Publishes to:  parking/{lot_id}/charger/{charger_id}/power
"""

import json
import time
import random
import math
from datetime import datetime, timezone

import boto3
from config import (
    AWS_REGION, SQS_QUEUE_URL, LOT_ID,
    TOTAL_CHARGERS, POWER_DRAW_INTERVAL, MAX_POWER_KW
)


class PowerDrawSensor:
    def __init__(self, charger_id: str):
        self.charger_id = charger_id
        self.power_kw = 0.0
        self.energy_kwh = 0.0
        self.charging = False
        self.session_tick = 0          # ticks since charge started
        self.session_length = 0        # total ticks for this session

    def start_session(self):
        self.charging = True
        self.session_tick = 0
        self.session_length = random.randint(60, 300)   # 5–25 min in ticks
        self.energy_kwh = 0.0

    def stop_session(self):
        self.charging = False
        self.power_kw = 0.0
        self.session_tick = 0

    def tick(self) -> dict:
        if self.charging:
            progress = self.session_tick / max(self.session_length, 1)
            if progress < 0.1:
                # Ramp-up
                self.power_kw = MAX_POWER_KW * (progress / 0.1) + random.uniform(-0.3, 0.3)
            elif progress < 0.75:
                # Constant current
                self.power_kw = MAX_POWER_KW + random.uniform(-0.5, 0.5)
            elif progress < 0.95:
                # Taper
                taper = 1 - ((progress - 0.75) / 0.20)
                self.power_kw = MAX_POWER_KW * taper + random.uniform(-0.3, 0.3)
            else:
                # Complete / trickle
                self.power_kw = random.uniform(0.0, 0.3)

            self.power_kw = max(0.0, self.power_kw)
            self.energy_kwh += self.power_kw * (POWER_DRAW_INTERVAL / 3600)
            self.session_tick += 1

            if self.session_tick >= self.session_length:
                self.stop_session()
        else:
            self.power_kw = 0.0
            # Randomly start a new session
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
    sqs = boto3.client('sqs', region_name=AWS_REGION)


    sensors = [PowerDrawSensor(f"CHG-{i:02d}") for i in range(1, TOTAL_CHARGERS + 1)]
    print(f"[PowerDraw] Simulating {len(sensors)} chargers  →  "
          f"publishing every {POWER_DRAW_INTERVAL}s")

    try:
        while True:
            for s in sensors:
                reading = s.tick()
                topic = f"parking/{LOT_ID}/charger/{s.charger_id}/power"
                
                sqs_payload = {"topic": topic, "payload": reading}
                sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_payload))
                
            time.sleep(POWER_DRAW_INTERVAL)
    except KeyboardInterrupt:
        print("[PowerDraw] Shutting down …")
    except Exception as e:
        print(f"[PowerDraw] SQS Error: {e}")


if __name__ == "__main__":
    run()
