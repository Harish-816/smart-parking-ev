"""
Cloud API Server
────────────────
Flask REST API + MQTT subscriber that writes fog data to SQLite.
Serves dashboard endpoints for parking, chargers, environment.
"""

import json
import sys
import os
import time
import threading
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager

from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt

# Add sensor config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sensors"))
from config import MQTT_BROKER, MQTT_PORT, LOT_ID, TOTAL_SPOTS, TOTAL_CHARGERS

# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(__file__), "smart_parking.db")


def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            spot_id    TEXT PRIMARY KEY,
            lot_id     TEXT,
            occupied   INTEGER DEFAULT 0,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS charger_status (
            charger_id TEXT PRIMARY KEY,
            lot_id     TEXT,
            status     TEXT DEFAULT 'available',
            power_kw   REAL DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            vehicle_id TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS occupancy_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id      TEXT,
            total_spots INTEGER,
            occupied    INTEGER,
            available   INTEGER,
            occ_pct     REAL,
            recorded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS energy_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id          TEXT,
            total_kwh       REAL,
            active_sessions INTEGER,
            recorded_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS environment_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id      TEXT,
            avg_temp_c  REAL,
            avg_humidity REAL,
            avg_lux     REAL,
            recorded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS blocked_alerts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            charger_id    TEXT,
            blocked_since TEXT,
            duration_min  REAL,
            resolved      INTEGER DEFAULT 0,
            recorded_at   TEXT
        );
    """)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# MQTT SUBSCRIBER  (runs in a background thread)
# ═══════════════════════════════════════════════════════════════
def mqtt_on_connect(client, userdata, flags, rc):
    print(f"[Cloud-MQTT] Connected (rc={rc})")
    client.subscribe(f"fog/parking/{LOT_ID}/#")
    client.subscribe(f"parking/{LOT_ID}/charger/+/status")


def mqtt_on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    topic = msg.topic
    now = datetime.now(timezone.utc).isoformat()

    try:
        # ── Smoothed per-spot occupancy ──
        if "/spot/" in topic and topic.endswith("/occupancy") and "fog/" in topic:
            spot_id = payload.get("spot_id", "")
            occupied = 1 if payload.get("occupied") else 0
            with get_db() as db:
                db.execute("""
                    INSERT INTO parking_spots (spot_id, lot_id, occupied, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(spot_id) DO UPDATE SET occupied=?, updated_at=?
                """, (spot_id, LOT_ID, occupied, now, occupied, now))

        # ── Aggregated occupancy summary ──
        elif topic.endswith("/occupancy/smoothed"):
            with get_db() as db:
                db.execute("""
                    INSERT INTO occupancy_history
                    (lot_id, total_spots, occupied, available, occ_pct, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    LOT_ID,
                    payload.get("total_spots", TOTAL_SPOTS),
                    payload.get("occupied", 0),
                    payload.get("available", 0),
                    payload.get("occupancy_pct", 0),
                    now
                ))

        # ── Charger usage stats ──
        elif topic.endswith("/charger/usage_stats"):
            details = payload.get("charger_details", [])
            with get_db() as db:
                for ch in details:
                    cid = ch.get("charger_id", "")
                    db.execute("""
                        INSERT INTO charger_status
                        (charger_id, lot_id, status, power_kw, is_blocked, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(charger_id) DO UPDATE SET
                        status=?, power_kw=?, is_blocked=?, updated_at=?
                    """, (
                        cid, LOT_ID, ch.get("status"), ch.get("power_kw", 0),
                        1 if ch.get("is_blocked") else 0, now,
                        ch.get("status"), ch.get("power_kw", 0),
                        1 if ch.get("is_blocked") else 0, now
                    ))
                # energy history
                db.execute("""
                    INSERT INTO energy_history
                    (lot_id, total_kwh, active_sessions, recorded_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    LOT_ID,
                    payload.get("total_energy_kwh", 0),
                    payload.get("active_sessions", 0),
                    now
                ))

        # ── Charger status from raw sensor (for vehicle_id) ──
        elif "/charger/" in topic and topic.endswith("/status") and "fog/" not in topic:
            cid = payload.get("charger_id", "")
            with get_db() as db:
                db.execute("""
                    INSERT INTO charger_status
                    (charger_id, lot_id, status, vehicle_id, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(charger_id) DO UPDATE SET
                    status=?, vehicle_id=?, updated_at=?
                """, (
                    cid, LOT_ID, payload.get("status"), payload.get("vehicle_id"), now,
                    payload.get("status"), payload.get("vehicle_id"), now
                ))

        # ── Blocked charger alert ──
        elif topic.endswith("/charger/blocked"):
            with get_db() as db:
                db.execute("""
                    INSERT INTO blocked_alerts
                    (charger_id, blocked_since, duration_min, recorded_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    payload.get("charger_id"),
                    payload.get("blocked_since"),
                    payload.get("duration_min"),
                    now
                ))

        # ── Environment summary ──
        elif topic.endswith("/environment/summary"):
            with get_db() as db:
                db.execute("""
                    INSERT INTO environment_history
                    (lot_id, avg_temp_c, avg_humidity, avg_lux, recorded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    LOT_ID,
                    payload.get("avg_temp_c", 0),
                    payload.get("avg_humidity_pct", 0),
                    payload.get("avg_lux", 0),
                    now
                ))
    except Exception as e:
        print(f"[Cloud-MQTT] DB error: {e}")


def start_mqtt():
    mc = mqtt.Client(client_id="cloud-api-mqtt", protocol=mqtt.MQTTv311)
    mc.on_connect = mqtt_on_connect
    mc.on_message = mqtt_on_message
    mc.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mc.loop_forever()


# ═══════════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
CORS(app)


@app.route("/api/parking/availability")
def parking_availability():
    with get_db() as db:
        rows = db.execute(
            "SELECT spot_id, occupied, updated_at FROM parking_spots ORDER BY spot_id"
        ).fetchall()
    spots = [dict(r) for r in rows]
    occupied = sum(1 for s in spots if s["occupied"])
    return jsonify({
        "lot_id": LOT_ID,
        "total_spots": TOTAL_SPOTS,
        "occupied": occupied,
        "available": TOTAL_SPOTS - occupied,
        "spots": spots
    })


@app.route("/api/parking/occupancy-history")
def occupancy_history():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM occupancy_history ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/chargers/status")
def chargers_status():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM charger_status ORDER BY charger_id"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/chargers/energy")
def chargers_energy():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM energy_history ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/chargers/blocked")
def chargers_blocked():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM blocked_alerts WHERE resolved=0 ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/environment/current")
def environment_current():
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM environment_history ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return jsonify(dict(row) if row else {})


@app.route("/api/environment/history")
def environment_history():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM environment_history ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/dashboard/summary")
def dashboard_summary():
    with get_db() as db:
        # Occupancy
        spots = db.execute("SELECT * FROM parking_spots").fetchall()
        occupied = sum(1 for s in spots if s["occupied"])

        # Chargers
        chargers = db.execute("SELECT * FROM charger_status ORDER BY charger_id").fetchall()

        # Latest energy
        energy = db.execute(
            "SELECT * FROM energy_history ORDER BY id DESC LIMIT 1"
        ).fetchone()

        # Latest environment
        env = db.execute(
            "SELECT * FROM environment_history ORDER BY id DESC LIMIT 1"
        ).fetchone()

        # Active blocked alerts
        blocked = db.execute(
            "SELECT * FROM blocked_alerts WHERE resolved=0"
        ).fetchall()

    return jsonify({
        "parking": {
            "total_spots": TOTAL_SPOTS,
            "occupied": occupied,
            "available": TOTAL_SPOTS - occupied,
            "occupancy_pct": round(occupied / TOTAL_SPOTS * 100, 1) if TOTAL_SPOTS else 0
        },
        "chargers": [dict(c) for c in chargers],
        "energy": dict(energy) if energy else {},
        "environment": dict(env) if env else {},
        "blocked_alerts": [dict(b) for b in blocked],
        "total_chargers": TOTAL_CHARGERS
    })


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    print("[Cloud] Database initialized")

    # Start MQTT subscriber in background thread
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    print("[Cloud] MQTT subscriber started")

    print("[Cloud] Starting Flask API on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
