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

import boto3
from config import (
    AWS_REGION, SQS_QUEUE_URL, LOT_ID,
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
    sqs = boto3.client('sqs', region_name=AWS_REGION)


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
                
                # Wrap the topic and reading into a single SQS payload
                sqs_payload = {"topic": topic, "payload": reading}
                sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_payload))
                
            time.sleep(OCCUPANCY_INTERVAL)
    except KeyboardInterrupt:
        print("[Occupancy] Shutting down …")
    except Exception as e:
        print(f"[Occupancy] SQS Error: {e}")


if __name__ == "__main__":
    run()
