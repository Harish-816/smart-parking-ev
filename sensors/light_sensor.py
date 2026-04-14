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

import boto3
from config import AWS_REGION, SQS_QUEUE_URL, LOT_ID, LIGHT_INTERVAL


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
    sqs = boto3.client('sqs', region_name=AWS_REGION)


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
            
            sqs_payload = {"topic": topic, "payload": payload}
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_payload))
            
            icon = "☀️" if daylight else "🌙"
            print(f"  {icon}  {lux} lux")
            time.sleep(LIGHT_INTERVAL)
    except KeyboardInterrupt:
        print("[Light] Shutting down …")
    except Exception as e:
        print(f"[Light] SQS Error: {e}")


if __name__ == "__main__":
    run()
