"""
Occupancy Smoother — Fog Layer
──────────────────────────────
Sliding-window debounce with hysteresis for parking occupancy.
"""

from collections import deque


class OccupancySmoother:
    """Per-spot sliding window smoother with majority voting + hysteresis."""

    def __init__(self, window_size: int = 5, hysteresis: int = 2):
        self.window_size = window_size
        self.hysteresis = hysteresis
        # spot_id → deque of booleans (True = occupied)
        self._windows: dict[str, deque] = {}
        # spot_id → current smoothed state
        self._state: dict[str, bool] = {}
        # spot_id → consecutive flips counter
        self._flip_count: dict[str, int] = {}

    def update(self, spot_id: str, raw_occupied: bool) -> bool:
        """Feed a new raw reading and return the smoothed state."""
        if spot_id not in self._windows:
            self._windows[spot_id] = deque(maxlen=self.window_size)
            self._state[spot_id] = raw_occupied
            self._flip_count[spot_id] = 0

        window = self._windows[spot_id]
        window.append(raw_occupied)

        # Majority voting
        occupied_count = sum(window)
        majority_occupied = occupied_count >= (len(window) / 2)

        # Hysteresis — only flip after consecutive disagreements
        if majority_occupied != self._state[spot_id]:
            self._flip_count[spot_id] += 1
            if self._flip_count[spot_id] >= self.hysteresis:
                self._state[spot_id] = majority_occupied
                self._flip_count[spot_id] = 0
        else:
            self._flip_count[spot_id] = 0

        return self._state[spot_id]

    def get_summary(self, lot_id: str, total_spots: int) -> dict:
        """Return aggregate occupancy for the lot."""
        occupied = sum(1 for v in self._state.values() if v)
        available = total_spots - occupied
        return {
            "lot_id": lot_id,
            "total_spots": total_spots,
            "occupied": occupied,
            "available": available,
            "occupancy_pct": round(occupied / total_spots * 100, 1) if total_spots else 0
        }
