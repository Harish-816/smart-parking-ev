module.exports = {
  apps: [
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
      script: "serve",
      env: {
        PM2_SERVE_PATH: 'dashboard/dist',
        PM2_SERVE_PORT: 8080,
        PM2_SERVE_SPA: 'true',
        PM2_SERVE_HOMEPAGE: '/index.html'
      }
    }
  ]
};
