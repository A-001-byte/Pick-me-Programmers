"""
ThreatSense-AI Utility Module.
Provides logging and OpenCV-based visualisation helpers.
"""

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

class Logger:
    """Standardises logging across the ThreatSense-AI application."""

    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")


# ---------------------------------------------------------------------------
# Colour palette (one per track ID)
# ---------------------------------------------------------------------------

_COLORS = [
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (128, 255, 0),
    (0, 128, 255),
    (255, 128, 0),
    (128, 0, 255),
]


def _color_for_id(track_id):
    return _COLORS[track_id % len(_COLORS)]


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_bounding_boxes(frame, detections):
    """
    Draw raw detection boxes on a frame.

    Parameters
    ----------
    frame      : np.ndarray – BGR image.
    detections : list – each element is [x1, y1, x2, y2, confidence].

    Returns
    -------
    frame : np.ndarray – image with overlays drawn in-place.
    """
    for det in detections:
        x1, y1, x2, y2 = int(det[0]), int(det[1]), int(det[2]), int(det[3])
        conf = det[4] if len(det) > 4 else 0.0
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"{conf:.2f}",
            (x1, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )
    return frame


def draw_tracked_objects(frame, tracked_objects):
    """
    Draw tracked-object boxes with behaviour overlays.

    Parameters
    ----------
    frame           : np.ndarray – BGR image.
    tracked_objects : list[dict] – output of BehaviorAnalyzer.analyze().
        Each dict may contain: id, bbox, speed, loitering, weapon_detected.

    Returns
    -------
    frame : np.ndarray
    """
    for obj in tracked_objects:
        tid = obj.get("id", 0)
        bbox = obj.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        color = _color_for_id(tid)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Build overlay label
        speed = obj.get("speed", 0.0)
        loiter = obj.get("loitering", False)
        weapon = obj.get("weapon_detected", False)
        label = f"ID:{tid} Speed:{speed:.1f} Loiter:{loiter} Weapon:{weapon}"

        # Draw background rectangle for readability
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            frame,
            label,
            (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0),
            1,
        )
    return frame


def draw_restricted_zones(frame, zones):
    """
    Draw semi-transparent red overlays for restricted zones.

    Parameters
    ----------
    frame : np.ndarray – BGR image.
    zones : list – each element is [x1, y1, x2, y2].

    Returns
    -------
    frame : np.ndarray
    """
    overlay = frame.copy()
    for zone in zones:
        x1, y1, x2, y2 = int(zone[0]), int(zone[1]), int(zone[2]), int(zone[3])
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            frame,
            "RESTRICTED",
            (x1 + 4, y1 + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
    return frame
