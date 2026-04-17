# ─── Sensor Configuration ───────────────────────────────────────
# Shared settings for all sensor simulators

# ─── Local MQTT Broker ─────────────────────────────────────────
MQTT_BROKER = "localhost"
MQTT_PORT   = 1883

# (AWS settings kept for reference — not used in local mode)
AWS_REGION = "us-east-1"
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/730679665100/SmartParkingDataQueue")
USE_SQS = os.environ.get("USE_SQS", "0").strip().lower() in ("1", "true", "yes")
LOT_ID = "LOT-1"

# ─── Intervals (seconds) ───────────────────────────────────────
OCCUPANCY_INTERVAL = 3
CHARGER_STATUS_INTERVAL = 10
POWER_DRAW_INTERVAL = 5
TEMPERATURE_INTERVAL = 30
LIGHT_INTERVAL = 30

# ─── Parking Lot Layout ────────────────────────────────────────
TOTAL_SPOTS = 50
TOTAL_CHARGERS = 8

# ─── Occupancy Sensor ──────────────────────────────────────────
OCCUPANCY_THRESHOLD_CM = 30        # < 30 cm → spot is occupied
OCCUPANCY_NOISE_PROB = 0.05        # 5 % chance of a noisy reading

# ─── Power Draw ────────────────────────────────────────────────
MAX_POWER_KW = 22.0                # Level 2 charger max
RAMP_DURATION_S = 120              # 2 min ramp-up
TAPER_START_PCT = 0.80             # taper begins at 80 % SoC

# ─── Blocked Charger ───────────────────────────────────────────
BLOCKED_THRESHOLD_MIN = 30         # minutes idle before "blocked"
BLOCKED_POWER_THRESHOLD_KW = 0.5   # power below this = idle
