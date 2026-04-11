"""
Blocked Charger Detector — Fog Layer
─────────────────────────────────────
Correlates charger status + power draw to detect blocked chargers.
A charger is "blocked" when it shows status = in_use but power < threshold
for longer than BLOCKED_THRESHOLD_MIN minutes.
"""

import time
from datetime import datetime, timezone


class BlockedChargerDetector:
    """Detect chargers that are blocked (vehicle done charging but not moved)."""

    def __init__(self, power_threshold_kw: float = 0.5, blocked_after_min: float = 2.0):
        self.power_threshold = power_threshold_kw
        self.blocked_after_s = blocked_after_min * 60  # convert to seconds
        # charger_id → {"status": str, "power_kw": float,
        #               "idle_since": float|None, "blocked": bool}
        self._chargers: dict[str, dict] = {}

    def update_status(self, charger_id: str, status: str):
        """Update known charger status."""
        if charger_id not in self._chargers:
            self._chargers[charger_id] = {
                "status": status, "power_kw": 0.0,
                "idle_since": None, "blocked": False
            }
        self._chargers[charger_id]["status"] = status

        # If charger went to available / offline, clear everything
        if status in ("available", "offline"):
            self._chargers[charger_id]["idle_since"] = None
            self._chargers[charger_id]["blocked"] = False

    def update_power(self, charger_id: str, power_kw: float):
        """Update known power reading and check blocked condition."""
        if charger_id not in self._chargers:
            self._chargers[charger_id] = {
                "status": "unknown", "power_kw": power_kw,
                "idle_since": None, "blocked": False
            }

        ch = self._chargers[charger_id]
        ch["power_kw"] = power_kw

        # Check idle condition: status is in_use but power is near zero
        if ch["status"] == "in_use" and power_kw < self.power_threshold:
            if ch["idle_since"] is None:
                ch["idle_since"] = time.time()
        else:
            ch["idle_since"] = None
            ch["blocked"] = False

    def check_blocked(self) -> list[dict]:
        """Return list of newly-blocked charger alerts."""
        alerts = []
        now = time.time()
        for cid, ch in self._chargers.items():
            if ch["idle_since"] and not ch["blocked"]:
                idle_duration = now - ch["idle_since"]
                if idle_duration >= self.blocked_after_s:
                    ch["blocked"] = True
                    alerts.append({
                        "charger_id": cid,
                        "blocked_since": datetime.fromtimestamp(
                            ch["idle_since"], tz=timezone.utc
                        ).isoformat(),
                        "duration_min": round(idle_duration / 60, 1),
                        "alert": True,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        return alerts

    def get_all_status(self) -> list[dict]:
        """Return current status of all known chargers."""
        return [
            {
                "charger_id": cid,
                "status": "blocked" if ch["blocked"] else ch["status"],
                "power_kw": ch["power_kw"],
                "is_blocked": ch["blocked"]
            }
            for cid, ch in sorted(self._chargers.items())
        ]
