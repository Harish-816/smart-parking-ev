module.exports = {
  apps: [
    {
      name: "mqtt-broker",
      script: ".venv/bin/python",
      args: "mqtt_broker.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "cloud-api",
      script: ".venv/bin/python",
      args: "cloud/server.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "fog-node",
      script: ".venv/bin/python",
      args: "fog/fog_node.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "sensor-occupancy",
      script: ".venv/bin/python",
      args: "sensors/occupancy_sensor.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "sensor-charger",
      script: ".venv/bin/python",
      args: "sensors/charger_status_sensor.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "sensor-power",
      script: ".venv/bin/python",
      args: "sensors/power_draw_sensor.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "sensor-temp",
      script: ".venv/bin/python",
      args: "sensors/temperature_sensor.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "sensor-light",
      script: ".venv/bin/python",
      args: "sensors/light_sensor.py",
      interpreter: "none",
      watch: false
    },
    {
      name: "dashboard",
      script: "npm",
      args: "run dev -- --host 0.0.0.0",
      cwd: "./dashboard",
      interpreter: "none",
      watch: false
    }
  ]
};
