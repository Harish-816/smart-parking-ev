import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Triggered by API Gateway (HTTP GET).
    Fetches the latest data from DynamoDB and returns the dashboard summary.
    """
    print(f"[DEBUG] Event received: {json.dumps(event)}")
    
    try:
        parking_table = dynamodb.Table('ParkingSpots')
        charger_table = dynamodb.Table('ChargerStatus')
        env_table = dynamodb.Table('Environment')

        # ── Parking Occupancy ──
        print("[DEBUG] Scanning ParkingSpots...")
        spots_response = parking_table.scan()
        spots = spots_response.get('Items', [])
        total_spots = 50
        occupied = sum(1 for spot in spots if spot.get('occupied'))
        print(f"[DEBUG] Found {len(spots)} spots, {occupied} occupied")

        # ── Charger Status ──
        print("[DEBUG] Scanning ChargerStatus...")
        chargers_response = charger_table.scan()
        chargers = chargers_response.get('Items', [])
        print(f"[DEBUG] Found {len(chargers)} chargers")

        # ── Environment ──
        print("[DEBUG] Scanning Environment...")
        env_response = env_table.scan()
        env_items = env_response.get('Items', [])
        temp_data = next((item for item in env_items if item.get('type') == 'temperature'), {})
        light_data = next((item for item in env_items if item.get('type') == 'light'), {})

        environment = {
            "avg_temp_c": float(temp_data.get('temp_c', 0)),
            "avg_humidity_pct": float(temp_data.get('humidity_pct', 0)),
            "avg_lux": float(light_data.get('lux', 0))
        }

        # ── Construct Dashboard Summary ──
        summary = {
            "parking": {
                "total_spots": total_spots,
                "occupied": occupied,
                "available": max(0, total_spots - occupied),
                "occupancy_pct": round(occupied / total_spots * 100, 1) if total_spots else 0
            },
            "chargers": chargers,
            "environment": environment,
            "total_chargers": len(chargers),
            "blocked_alerts": []
        }

        print("[DEBUG] Successfully built summary, returning response")
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Content-Type": "application/json"
            },
            "body": json.dumps(summary, cls=DecimalEncoder)
        }

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] Exception: {e}")
        print(f"[ERROR] Traceback: {error_detail}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e), "detail": error_detail})
        }

