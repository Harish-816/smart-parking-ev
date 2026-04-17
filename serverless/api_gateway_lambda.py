import json
import boto3
import os
from decimal import Decimal

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
dynamodb   = boto3.resource('dynamodb', region_name=AWS_REGION)

PARKING_TABLE = os.environ.get('PARKING_TABLE', 'ParkingSpots')
CHARGER_TABLE = os.environ.get('CHARGER_TABLE', 'ChargerStatus')
ENV_TABLE     = os.environ.get('ENV_TABLE', 'Environment')

CORS_HEADERS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Content-Type':                 'application/json'
}


class DecimalEncoder(json.JSONEncoder):
    """Convert DynamoDB Decimal types to int/float for JSON serialisation."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def _success(body: dict) -> dict:
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def _error(status: int, message: str) -> dict:
    return {
        'statusCode': status,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': message})
    }


def lambda_handler(event, context):
    """
    Triggered by API Gateway HTTP API.
    Routes:
      GET /dashboard/summary    → full summary (parking + chargers + environment)
      GET /parking/availability → parking spots only
      GET /chargers/status      → charger statuses only
      OPTIONS *                 → CORS preflight
    """
    print(f"[DEBUG] Event: {json.dumps(event)}")

    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path   = event.get('rawPath', '/dashboard/summary')

    # ── CORS Preflight ──────────────────────────────────────────────────────
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    try:
        parking_table = dynamodb.Table(PARKING_TABLE)
        charger_table = dynamodb.Table(CHARGER_TABLE)
        env_table     = dynamodb.Table(ENV_TABLE)

        # ── /parking/availability ──────────────────────────────────────────
        if path == '/parking/availability':
            spots_resp = parking_table.scan()
            spots      = spots_resp.get('Items', [])
            total      = 50
            occupied   = sum(1 for s in spots if s.get('occupied'))
            return _success({
                'lot_id':        'LOT-1',
                'total_spots':   total,
                'occupied':      occupied,
                'available':     max(0, total - occupied),
                'occupancy_pct': round(occupied / total * 100, 1) if total else 0,
                'spots':         spots
            })

        # ── /chargers/status ───────────────────────────────────────────────
        if path == '/chargers/status':
            chargers_resp = charger_table.scan()
            chargers      = chargers_resp.get('Items', [])
            return _success({'chargers': chargers})

        # ── /dashboard/summary (default) ───────────────────────────────────
        print("[DEBUG] Scanning ParkingSpots...")
        spots_resp = parking_table.scan()
        spots      = spots_resp.get('Items', [])
        total      = 50
        occupied   = sum(1 for s in spots if s.get('occupied'))
        print(f"[DEBUG] Spots: {len(spots)} total, {occupied} occupied")

        print("[DEBUG] Scanning ChargerStatus...")
        chargers_resp = charger_table.scan()
        chargers      = chargers_resp.get('Items', [])
        print(f"[DEBUG] Chargers: {len(chargers)}")

        print("[DEBUG] Scanning Environment...")
        env_resp  = env_table.scan()
        env_items = env_resp.get('Items', [])

        temp_data  = next((i for i in env_items if i.get('type') == 'temperature'), {})
        light_data = next((i for i in env_items if i.get('type') == 'light'), {})

        environment = {
            'avg_temp_c':      float(temp_data.get('temp_c', 0)),
            'avg_humidity_pct': float(temp_data.get('humidity_pct', 0)),
            'avg_lux':         float(light_data.get('lux', 0)),
            'daylight':        bool(light_data.get('daylight', False))
        }

        # Blocked chargers (chargers in 'blocked' status)
        blocked = [c for c in chargers if c.get('status') == 'blocked']

        summary = {
            'parking': {
                'total_spots':   total,
                'occupied':      occupied,
                'available':     max(0, total - occupied),
                'occupancy_pct': round(occupied / total * 100, 1) if total else 0
            },
            'chargers':        chargers,
            'energy':          {},
            'environment':     environment,
            'blocked_alerts':  blocked,
            'total_chargers':  len(chargers)
        }

        print("[DEBUG] Summary built successfully")
        return _success(summary)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] {e}\n{tb}")
        return _error(500, str(e))
