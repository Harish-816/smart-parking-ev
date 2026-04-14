import json
import boto3
import os
from datetime import datetime, timezone

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Triggered by SQS. Processes raw incoming sensor data and updates DynamoDB.
    """
    parking_table = dynamodb.Table(os.environ.get('PARKING_TABLE', 'ParkingSpots'))
    charger_table = dynamodb.Table(os.environ.get('CHARGER_TABLE', 'ChargerStatus'))
    env_table = dynamodb.Table(os.environ.get('ENV_TABLE', 'Environment'))
    
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            topic = body.get('topic', '')
            payload = body.get('payload', {})
            
            # ── Occupancy ──
            if "/spot/" in topic and topic.endswith("/occupancy"):
                parking_table.put_item(
                    Item={
                        'spot_id': payload.get('spot_id'),
                        'lot_id': payload.get('lot_id'),
                        'occupied': payload.get('occupied', False),
                        'distance_cm': str(payload.get('distance_cm', 0)),
                        'updated_at': payload.get('timestamp')
                    }
                )
                
            # ── Charger Status ──
            elif "/charger/" in topic and topic.endswith("/status"):
                charger_table.update_item(
                    Key={'charger_id': payload.get('charger_id')},
                    UpdateExpression="SET lot_id = :l, #st = :s, vehicle_id = :v, updated_at = :u",
                    ExpressionAttributeNames={'#st': 'status'},
                    ExpressionAttributeValues={
                        ':l': payload.get('lot_id'),
                        ':s': payload.get('status'),
                        ':v': payload.get('vehicle_id'),
                        ':u': payload.get('timestamp')
                    }
                )
                
            # ── Power Draw ──
            elif "/charger/" in topic and topic.endswith("/power"):
                # We update the same charger table with power fields
                charger_table.update_item(
                    Key={'charger_id': payload.get('charger_id')},
                    UpdateExpression="SET power_kw = :p, energy_kwh = :e, updated_at = :u",
                    ExpressionAttributeValues={
                        ':p': str(payload.get('power_kw')),
                        ':e': str(payload.get('energy_kwh')),
                        ':u': payload.get('timestamp')
                    }
                )
                
            # ── Temperature ──
            elif topic.endswith("/environment/temperature"):
                env_table.put_item(
                    Item={
                        'lot_id': payload.get('lot_id'),
                        'type': 'temperature',
                        'temp_c': str(payload.get('temp_c')),
                        'humidity_pct': str(payload.get('humidity_pct')),
                        'updated_at': payload.get('timestamp')
                    }
                )
                
            # ── Light ──
            elif topic.endswith("/environment/light"):
                env_table.put_item(
                    Item={
                        'lot_id': payload.get('lot_id'),
                        'type': 'light',
                        'lux': str(payload.get('lux')),
                        'daylight': payload.get('daylight'),
                        'updated_at': payload.get('timestamp')
                    }
                )
                
        except Exception as e:
            print(f"Error processing record: {e}")
            
    return {
        "statusCode": 200,
        "body": json.dumps("Ingestion complete")
    }
