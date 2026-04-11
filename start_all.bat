@echo off
setlocal

echo Starting Smart Parking + EV Charger Status Project...

:: Start Mosquitto in a new window using mqtt_broker.py
echo Starting Mosquitto Broker...
start "Mosquitto Broker" .venv\Scripts\python mqtt_broker.py
timeout /t 2 /nobreak >nul

:: Start Cloud API
echo Starting Cloud API Server...
start "Cloud API" .venv\Scripts\python cloud/server.py
timeout /t 3 /nobreak >nul

:: Start Fog Node
echo Starting Fog Node...
start "Fog Node" .venv\Scripts\python fog/fog_node.py
timeout /t 2 /nobreak >nul

:: Start Sensors
echo Starting Sensors...
start "Sensors - Occupancy" .venv\Scripts\python sensors/occupancy_sensor.py
start "Sensors - Charger Status" .venv\Scripts\python sensors/charger_status_sensor.py
start "Sensors - Power Draw" .venv\Scripts\python sensors/power_draw_sensor.py
start "Sensors - Environment" .venv\Scripts\python sensors/temperature_sensor.py
start "Sensors - Light" .venv\Scripts\python sensors/light_sensor.py

:: Start Dashboard
echo Starting Dashboard...
cd dashboard
start "Dashboard" npm run dev

echo All components started! 
echo Dashboard: http://localhost:5173
echo Cloud API: http://localhost:5000
pause
