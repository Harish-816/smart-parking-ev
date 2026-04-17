import json
import boto3
import os
from decimal import Decimal
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

PARKING_TABLE = os.environ.get('PARKING_TABLE', 'ParkingSpots')
CHARGER_TABLE = os.environ.get('CHARGER_TABLE', 'ChargerStatus')
ENV_TABLE     = os.environ.get('ENV_TABLE', 'Environment')


class DecimalEncoder(json.JSONEncoder):
    """Convert DynamoDB Decimal types to int/float for JSON serialisation."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Triggered by SQS. Processes raw incoming sensor data and updates DynamoDB.
    Each SQS message body must be: { "topic": "...", "payload": { ... } }
    """
    parking_table = dynamodb.Table(PARKING_TABLE)
    charger_table = dynamodb.Table(CHARGER_TABLE)
    env_table     = dynamodb.Table(ENV_TABLE)

    failed_records = []

    for record in event.get('Records', []):
        try:
            body    = json.loads(record['body'])
            topic   = body.get('topic', '')
            payload = body.get('payload', {})
            now     = datetime.now(timezone.utc).isoformat()

            # ── Occupancy ────────────────────────────────────────────────────
            if '/spot/' in topic and topic.endswith('/occupancy'):
                parking_table.put_item(
                    Item={
                        'spot_id':     payload.get('spot_id', 'unknown'),
                        'lot_id':      payload.get('lot_id', 'LOT-1'),
                        'occupied':    bool(payload.get('occupied', False)),
                        'distance_cm': Decimal(str(payload.get('distance_cm', 0))),
                        'updated_at':  payload.get('timestamp', now)
                    }
                )

            # ── Charger Status ────────────────────────────────────────────────
            elif '/charger/' in topic and topic.endswith('/status'):
                charger_table.update_item(
                    Key={'charger_id': payload.get('charger_id', 'unknown')},
                    UpdateExpression=(
                        "SET lot_id = :l, #st = :s, vehicle_id = :v, updated_at = :u"
                    ),
                    ExpressionAttributeNames={'#st': 'status'},
                    ExpressionAttributeValues={
                        ':l': payload.get('lot_id', 'LOT-1'),
                        ':s': payload.get('status', 'unknown'),
                        ':v': payload.get('vehicle_id'),
                        ':u': payload.get('timestamp', now)
                    }
                )

            # ── Power Draw ────────────────────────────────────────────────────
            elif '/charger/' in topic and topic.endswith('/power'):
                charger_table.update_item(
                    Key={'charger_id': payload.get('charger_id', 'unknown')},
                    UpdateExpression=(
                        "SET power_kw = :p, energy_kwh = :e, updated_at = :u"
                    ),
                    ExpressionAttributeValues={
                        ':p': Decimal(str(payload.get('power_kw', 0))),
                        ':e': Decimal(str(payload.get('energy_kwh', 0))),
                        ':u': payload.get('timestamp', now)
                    }
                )

            # ── Temperature ────────────────────────────────────────────────────
            elif topic.endswith('/environment/temperature'):
                env_table.put_item(
                    Item={
                        'lot_id':       payload.get('lot_id', 'LOT-1'),
                        'type':         'temperature',
                        'temp_c':       Decimal(str(payload.get('temp_c', 0))),
                        'humidity_pct': Decimal(str(payload.get('humidity_pct', 0))),
                        'updated_at':   payload.get('timestamp', now)
                    }
                )

            # ── Light ─────────────────────────────────────────────────────────
            elif topic.endswith('/environment/light'):
                env_table.put_item(
                    Item={
                        'lot_id':     payload.get('lot_id', 'LOT-1'),
                        'type':       'light',
                        'lux':        Decimal(str(payload.get('lux', 0))),
                        'daylight':   bool(payload.get('daylight', False)),
                        'updated_at': payload.get('timestamp', now)
                    }
                )

            else:
                print(f"[WARN] Unknown topic pattern: {topic} — skipping")

        except Exception as e:
            print(f"[ERROR] Failed to process record: {e}")
            print(f"[ERROR] Record body: {record.get('body', 'N/A')[:500]}")
            # Report as partial failure so SQS retries only failed messages
            failed_records.append({'itemIdentifier': record['messageId']})

    if failed_records:
        return {'batchItemFailures': failed_records}

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Ingestion complete', 'processed': len(event.get('Records', []))})
    }
