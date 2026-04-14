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

import boto3
from config import AWS_REGION, SQS_QUEUE_URL, LOT_ID, TEMPERATURE_INTERVAL


def get_simulated_temperature() -> tuple:
    """Return (temp_c, humidity_pct) following a daily cycle."""
    hour = datetime.now().hour + datetime.now().minute / 60.0
    # Base temperature: sinusoidal cycle peaking at ~14:00
    base_temp = 25 + 8 * math.sin(math.pi * (hour - 6) / 12)
    temp_c = base_temp + random.uniform(-1.0, 1.0)

    # Humidity inversely correlated with temp
    humidity = 60 - 15 * math.sin(math.pi * (hour - 6) / 12) + random.uniform(-5, 5)
    humidity = max(20, min(95, humidity))

    return round(temp_c, 1), round(humidity, 1)


def run():
    sqs = boto3.client('sqs', region_name=AWS_REGION)


    print(f"[Temperature] Publishing every {TEMPERATURE_INTERVAL}s")

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
            
            sqs_payload = {"topic": topic, "payload": payload}
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_payload))
            
            print(f"  🌡️  {temp_c}°C  |  💧 {humidity_pct}%")
            time.sleep(TEMPERATURE_INTERVAL)
    except KeyboardInterrupt:
        print("[Temperature] Shutting down …")
    except Exception as e:
        print(f"[Temperature] SQS Error: {e}")


if __name__ == "__main__":
    run()
