"""
Behavior Analysis Engine for ThreatSense-AI.
Analyses tracked persons to detect loitering, zone intrusion, weapon presence,
crowd density, and movement speed.
"""

import math
from collections import deque


class BehaviorAnalyzer:
    """
    Analyses tracked objects and returns per-person behaviour signals.

    Parameters
    ----------
    history_window   : int   – number of frames kept per person (default 60).
    loiter_threshold : float – max displacement (px) to count as stationary (default 40).
    loiter_frames    : int   – consecutive stationary frames to flag loitering (default 30).
    crowd_threshold  : int   – person count to raise a crowd alert (default 5).
    """

    def __init__(
        self,
        history_window=60,
        loiter_threshold=40,
        loiter_frames=30,
        crowd_threshold=5,
    ):
        self.history_window = history_window
        self.loiter_threshold = loiter_threshold
        self.loiter_frames = loiter_frames
        self.crowd_threshold = crowd_threshold

        # per-person state
        self.person_history: dict[int, deque] = {}   # id → deque of bbox centres
        self.weapon_flags: dict[int, bool] = {}       # id → weapon detected

        # zone & weapon definitions
        self.restricted_zones: list[list[float]] = []  # [[x1,y1,x2,y2], ...]

    # ----- configuration ----------------------------------------------------

    def set_zones(self, zones):
        """Set restricted zones as list of [x1, y1, x2, y2]."""
        self.restricted_zones = zones

    def set_weapon_flag(self, person_id, flag=True):
        """Manually mark a person as carrying a weapon."""
        self.weapon_flags[person_id] = flag

    def set_weapon_detections(self, weapon_bboxes):
        """
        Automatically flag any tracked person whose bbox overlaps a weapon bbox.

        Parameters
        ----------
        weapon_bboxes : list of [x1, y1, x2, y2]
        """
        for pid, history in self.person_history.items():
            if not history:
                continue
            cx, cy = history[-1]
            for wb in weapon_bboxes:
                if wb[0] <= cx <= wb[2] and wb[1] <= cy <= wb[3]:
                    self.weapon_flags[pid] = True
                    break

    # ----- main entry point -------------------------------------------------

    def analyze(self, tracked_objects):
        """
        Analyse a list of tracked objects for a single frame.

        Parameters
        ----------
        tracked_objects : list[dict]
            Each dict: {"id": int, "bbox": [x1, y1, x2, y2]}.

        Returns
        -------
        list[dict]
            Each dict contains:
            - id, bbox, speed, loitering, zone_intrusion,
              weapon_detected, crowd_density_alert.
        """
        crowd_alert = len(tracked_objects) >= self.crowd_threshold

        results = []
        for obj in tracked_objects:
            pid = obj["id"]
            bbox = obj["bbox"]
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            # Update history
            if pid not in self.person_history:
                self.person_history[pid] = deque(maxlen=self.history_window)
            self.person_history[pid].append((cx, cy))

            speed = self._compute_speed(pid)
            loitering = self._check_loitering(pid)
            zone_intrusion = self._check_zone_intrusion(cx, cy)
            weapon = self.weapon_flags.get(pid, False)

            results.append({
                "id": pid,
                "bbox": bbox,
                "speed": round(speed, 2),
                "loitering": loitering,
                "zone_intrusion": zone_intrusion,
                "weapon_detected": weapon,
                "crowd_density_alert": crowd_alert,
            })

        return results

    # ----- feature helpers --------------------------------------------------

    def _compute_speed(self, pid):
        """Euclidean displacement between the last two centres."""
        history = self.person_history[pid]
        if len(history) < 2:
            return 0.0
        (x1, y1), (x2, y2) = history[-2], history[-1]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def _check_loitering(self, pid):
        """
        True if the person's total displacement over the last
        ``loiter_frames`` frames stays below ``loiter_threshold``.
        """
        history = self.person_history[pid]
        if len(history) < self.loiter_frames:
            return False
        recent = list(history)[-self.loiter_frames:]
        x0, y0 = recent[0]
        x1, y1 = recent[-1]
        displacement = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        return displacement < self.loiter_threshold

    def _check_zone_intrusion(self, cx, cy):
        """True if the person centre is inside any restricted zone."""
        for zone in self.restricted_zones:
            x1, y1, x2, y2 = zone
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                return True
        return False
