"""
SQS Publisher Helper
────────────────────
Dual-path publisher: sends sensor data to AWS SQS (when USE_SQS=1 env var is set).
Used by all sensor simulators alongside MQTT publishing.
"""

import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Read from environment variable first, then fall back to config
SQS_QUEUE_URL = os.environ.get(
    "SQS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/614347200749/SmartParkingDataQueue"
)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Only create the SQS client if SQS is enabled, to avoid credential errors locally
_sqs_client = None


def _get_client():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    return _sqs_client


def is_sqs_enabled() -> bool:
    """Check if SQS publishing is enabled via environment variable."""
    return os.environ.get("USE_SQS", "0").strip().lower() in ("1", "true", "yes")


def send_to_sqs(topic: str, payload: dict) -> bool:
    """
    Send a sensor reading to SQS.

    Args:
        topic: MQTT-style topic string (e.g. 'parking/LOT-1/spot/SPOT-001/occupancy')
        payload: dict with sensor data

    Returns:
        True on success, False on failure (non-fatal — sensors continue with MQTT)
    """
    if not is_sqs_enabled():
        return False

    message = json.dumps({
        "topic": topic,
        "payload": payload
    })

    try:
        _get_client().send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message
        )
        return True
    except (BotoCoreError, ClientError) as e:
        print(f"[SQS] Warning: Failed to send message (topic={topic}): {e}")
        return False
    except Exception as e:
        print(f"[SQS] Unexpected error: {e}")
        return False
