"""
Fog Node — Main Entry Point
────────────────────────────
Subscribes to all raw sensor topics, runs processing logic,
and publishes processed data to fog/* topics.
"""

import json
import sys
import os
import time
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# Add parent dir so we can import sensors.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sensors"))
from config import (
    MQTT_BROKER, MQTT_PORT, LOT_ID, TOTAL_SPOTS, TOTAL_CHARGERS,
    BLOCKED_POWER_THRESHOLD_KW, BLOCKED_THRESHOLD_MIN
)

from occupancy_smoother import OccupancySmoother
from blocked_charger_detector import BlockedChargerDetector
from data_aggregator import DataAggregator

# ── Initialise processors ──────────────────────────────────────
smoother = OccupancySmoother(window_size=5, hysteresis=2)
blocked_detector = BlockedChargerDetector(
    power_threshold_kw=BLOCKED_POWER_THRESHOLD_KW,
    blocked_after_min=BLOCKED_THRESHOLD_MIN / 60   # use shorter time for demo (30s)
)
aggregator = DataAggregator()

client = mqtt.Client(client_id="fog-node", protocol=mqtt.MQTTv311)


# ── MQTT Callbacks ──────────────────────────────────────────────
def on_connect(c, userdata, flags, rc):
    print(f"[Fog] Connected to MQTT broker (rc={rc})")
    # Subscribe to all raw sensor topics
    c.subscribe(f"parking/{LOT_ID}/spot/+/occupancy")
    c.subscribe(f"parking/{LOT_ID}/charger/+/status")
    c.subscribe(f"parking/{LOT_ID}/charger/+/power")
    c.subscribe(f"parking/{LOT_ID}/environment/temperature")
    c.subscribe(f"parking/{LOT_ID}/environment/light")
    print("[Fog] Subscribed to all sensor topics")


def on_message(c, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    topic = msg.topic

    # ── Occupancy ────────────────────────────────────────────
    if "/spot/" in topic and topic.endswith("/occupancy"):
        spot_id = payload.get("spot_id", "")
        raw_occ = payload.get("occupied", False)
        smoothed = smoother.update(spot_id, raw_occ)

        # Publish per-spot smoothed
        c.publish(
            f"fog/parking/{LOT_ID}/spot/{spot_id}/occupancy",
            json.dumps({
                "spot_id": spot_id,
                "occupied": smoothed,
                "raw_occupied": raw_occ,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )

    # ── Charger status ───────────────────────────────────────
    elif "/charger/" in topic and topic.endswith("/status"):
        charger_id = payload.get("charger_id", "")
        status = payload.get("status", "")
        blocked_detector.update_status(charger_id, status)

    # ── Power draw ───────────────────────────────────────────
    elif "/charger/" in topic and topic.endswith("/power"):
        charger_id = payload.get("charger_id", "")
        power_kw = payload.get("power_kw", 0)
        energy_kwh = payload.get("energy_kwh", 0)
        blocked_detector.update_power(charger_id, power_kw)
        aggregator.update_energy(charger_id, energy_kwh)

    # ── Temperature ──────────────────────────────────────────
    elif topic.endswith("/environment/temperature"):
        aggregator.add_temperature(
            payload.get("temp_c", 0),
            payload.get("humidity_pct", 0)
        )

    # ── Light ────────────────────────────────────────────────
    elif topic.endswith("/environment/light"):
        aggregator.add_light(payload.get("lux", 0))


# ── Periodic publisher (runs in a thread) ───────────────────────
def periodic_publish():
    """Publish aggregated fog data every 10 seconds."""
    while True:
        time.sleep(10)

        # Occupancy summary
        summary = smoother.get_summary(LOT_ID, TOTAL_SPOTS)
        summary["timestamp"] = datetime.now(timezone.utc).isoformat()
        client.publish(
            f"fog/parking/{LOT_ID}/occupancy/smoothed",
            json.dumps(summary)
        )
        print(f"  🅿️  Occupancy: {summary['occupied']}/{summary['total_spots']}  "
              f"({summary['occupancy_pct']}%)")

        # Blocked charger alerts
        alerts = blocked_detector.check_blocked()
        for alert in alerts:
            client.publish(
                f"fog/parking/{LOT_ID}/charger/blocked",
                json.dumps(alert)
            )
            print(f"  🚨 BLOCKED: {alert['charger_id']}  "
                  f"({alert['duration_min']} min)")

        # Charger usage stats
        charger_statuses = blocked_detector.get_all_status()
        active = sum(1 for c in charger_statuses if c["status"] == "in_use")
        aggregator.set_active_sessions(active)
        energy_summary = aggregator.get_energy_summary()
        client.publish(
            f"fog/parking/{LOT_ID}/charger/usage_stats",
            json.dumps({
                "lot_id": LOT_ID,
                **energy_summary,
                "charger_details": charger_statuses
            })
        )

        # Environment summary
        env_summary = aggregator.get_environment_summary()
        env_summary["lot_id"] = LOT_ID
        client.publish(
            f"fog/parking/{LOT_ID}/environment/summary",
            json.dumps(env_summary)
        )

        aggregator.reset_environment()


# ── Main ────────────────────────────────────────────────────────
def run():
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    # Start periodic publisher in background
    t = threading.Thread(target=periodic_publish, daemon=True)
    t.start()

    print("[Fog] Fog node running — press Ctrl+C to stop")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("[Fog] Shutting down …")
    finally:
        client.disconnect()


if __name__ == "__main__":
    run()
