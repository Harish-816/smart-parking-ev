#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# EC2 Bootstrap Script — Smart Parking + EV Charger Status
# Run this ONCE on a fresh Ubuntu 22.04 EC2 instance as ec2-user / ubuntu
# Usage:  bash ec2_setup.sh  (after uploading or curling this file to EC2)
# ═══════════════════════════════════════════════════════════════════════════════
set -e  # Exit on any error

REPO_URL="https://github.com/Harish-816/smart-parking-ev.git"
APP_DIR="$HOME/smart-parking-ev"
BRANCH="main"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Smart Parking + EV Charger — EC2 Bootstrap         ║"
echo "╚══════════════════════════════════════════════════════╝"

# ─── 1. System update ─────────────────────────────────────────────────────────
echo "[1/9] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ─── 2. Install Python 3 ──────────────────────────────────────────────────────
echo "[2/9] Installing Python 3 + pip..."
sudo apt-get install -y python3 python3-venv python3-pip python3-dev build-essential

# ─── 3. Install Node.js 20 (LTS) ─────────────────────────────────────────────
echo "[3/9] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# ─── 4. Install PM2 ───────────────────────────────────────────────────────────
echo "[4/9] Installing PM2..."
sudo npm install -g pm2

# ─── 5. Install Mosquitto ─────────────────────────────────────────────────────
echo "[5/9] Installing Mosquitto MQTT broker..."
sudo apt-get install -y mosquitto mosquitto-clients

# Configure Mosquitto to allow anonymous connections on all interfaces
sudo bash -c 'cat > /etc/mosquitto/conf.d/smart-parking.conf << EOF
listener 1883 0.0.0.0
allow_anonymous true
EOF'
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
echo "    ✓ Mosquitto started on port 1883"

# ─── 6. Clone / Update repository ────────────────────────────────────────────
echo "[6/9] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "    Repository already exists — pulling latest..."
    cd "$APP_DIR"
    git fetch --all
    git reset --hard origin/$BRANCH
    git pull origin $BRANCH
else
    git clone -b $BRANCH "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# ─── 7. Python virtual environment ───────────────────────────────────────────
echo "[7/9] Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "    ✓ Python dependencies installed"
deactivate

# ─── 8. Build React dashboard ────────────────────────────────────────────────
echo "[8/9] Building React dashboard..."
cd "$APP_DIR/dashboard"
npm install --silent
npm run build
echo "    ✓ Dashboard built to dashboard/dist/"
cd "$APP_DIR"

# ─── 9. Start all services with PM2 ──────────────────────────────────────────
echo "[9/9] Starting all services with PM2..."

# Stop any existing PM2 processes cleanly
pm2 delete all 2>/dev/null || true

# Start using ecosystem config
pm2 start "$APP_DIR/ecosystem.config.js"

# Save PM2 process list and configure startup on reboot
pm2 save
pm2 startup systemd -u $USER --hp $HOME | tail -1 | sudo bash || true

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║           ✓ Deployment Complete!                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Services running:"
pm2 list
echo ""

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "check AWS console")
echo "  Dashboard URL:  http://$PUBLIC_IP:5000"
echo "  MQTT Broker:    $PUBLIC_IP:1883"
echo ""
echo "  To monitor logs:"
echo "    pm2 logs"
echo "    pm2 logs cloud-api"
echo "    pm2 monit"
