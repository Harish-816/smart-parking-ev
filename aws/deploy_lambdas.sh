#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Lambda Deployment Script — Smart Parking + EV Charger Status
# Run locally or in CI/CD. Requires AWS CLI configured with valid credentials.
# Usage:  bash aws/deploy_lambdas.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -e

REGION="${AWS_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVERLESS_DIR="$PROJECT_DIR/serverless"
TMP_DIR="$PROJECT_DIR/lambda_packages"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Smart Parking — Lambda Deployment                  ║"
echo "╚══════════════════════════════════════════════════════╝"

mkdir -p "$TMP_DIR"

# ─── Package fog_processor_lambda ─────────────────────────────────────────────
echo "[1/4] Packaging SmartParkingFogProcessor..."
cd "$SERVERLESS_DIR"
zip -j "$TMP_DIR/fog_processor.zip" fog_processor_lambda.py
echo "    ✓ fog_processor.zip created"

# ─── Deploy fog_processor_lambda ──────────────────────────────────────────────
echo "[2/4] Deploying SmartParkingFogProcessor to Lambda..."
aws lambda update-function-code \
    --function-name SmartParkingFogProcessor \
    --zip-file "fileb://$TMP_DIR/fog_processor.zip" \
    --region "$REGION" \
    --output table

# ─── Package api_gateway_lambda ───────────────────────────────────────────────
echo "[3/4] Packaging SmartParkingAPIHandler..."
zip -j "$TMP_DIR/api_handler.zip" api_gateway_lambda.py
echo "    ✓ api_handler.zip created"

# ─── Deploy api_gateway_lambda ────────────────────────────────────────────────
echo "[4/4] Deploying SmartParkingAPIHandler to Lambda..."
aws lambda update-function-code \
    --function-name SmartParkingAPIHandler \
    --zip-file "fileb://$TMP_DIR/api_handler.zip" \
    --region "$REGION" \
    --output table

# Cleanup
rm -rf "$TMP_DIR"

echo ""
echo "  ✓ Both Lambda functions updated successfully!"
echo ""
echo "  Verifying deployments..."
aws lambda list-functions \
    --region "$REGION" \
    --query "Functions[?contains(FunctionName,'SmartParking')].[FunctionName,LastModified,Runtime]" \
    --output table
