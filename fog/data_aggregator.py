"""
Data Aggregator — Fog Layer
───────────────────────────
Collects and combines processed data, pushes summaries periodically.
"""

from datetime import datetime, timezone


class DataAggregator:
    """Collect environment and usage data, produce periodic summaries."""

    def __init__(self):
        self._temperatures: list[float] = []
        self._humidities: list[float] = []
        self._lux_readings: list[float] = []
        self._energy_by_charger: dict[str, float] = {}
        self._active_sessions: int = 0
        self._total_vehicles_served: int = 0

    # ── Environment ──────────────────────────────────────────────
    def add_temperature(self, temp_c: float, humidity_pct: float):
        self._temperatures.append(temp_c)
        self._humidities.append(humidity_pct)

    def add_light(self, lux: float):
        self._lux_readings.append(lux)

    def get_environment_summary(self) -> dict:
        avg_temp = round(sum(self._temperatures) / len(self._temperatures), 1) if self._temperatures else 0
        avg_hum = round(sum(self._humidities) / len(self._humidities), 1) if self._humidities else 0
        avg_lux = round(sum(self._lux_readings) / len(self._lux_readings), 1) if self._lux_readings else 0
        return {
            "avg_temp_c": avg_temp,
            "avg_humidity_pct": avg_hum,
            "avg_lux": avg_lux,
            "temp_readings": len(self._temperatures),
            "lux_readings": len(self._lux_readings),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ── Charger Energy ───────────────────────────────────────────
    def update_energy(self, charger_id: str, energy_kwh: float):
        self._energy_by_charger[charger_id] = energy_kwh

    def set_active_sessions(self, count: int):
        self._active_sessions = count

    def get_energy_summary(self) -> dict:
        total = sum(self._energy_by_charger.values())
        return {
            "total_energy_kwh": round(total, 3),
            "per_charger": {k: round(v, 3) for k, v in sorted(self._energy_by_charger.items())},
            "active_sessions": self._active_sessions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ── Reset for next window ────────────────────────────────────
    def reset_environment(self):
        self._temperatures.clear()
        self._humidities.clear()
        self._lux_readings.clear()
