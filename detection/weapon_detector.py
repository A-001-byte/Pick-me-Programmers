"""
weapon_detector.py
──────────────────
Custom YOLO weapon detector.  Designed to run on **person crops** and
remap detected weapon bounding boxes back to full-frame coordinates.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

# (x1, y1, x2, y2, confidence, class_name)
WeaponDetection = Tuple[int, int, int, int, float, str]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT / "models" / "weapon_detector.pt"

# Classes to silently discard — "Gunmen" is a contextual label that
# causes false positives; "person" is already handled by PersonDetector.
IGNORED_CLASSES: set[str] = {"Gunmen", "person"}


class WeaponDetector:
    """Detect weapons inside cropped person regions."""

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL,
        device: int | str = 0,
        imgsz: int = 640,
    ) -> None:
        self.model = YOLO(str(model_path))
        self.device = device
        self.imgsz = imgsz

    # ── core detection on a raw crop ─────────────────────────────────

    def detect(
        self,
        crop: np.ndarray,
        conf: float = 0.3,
    ) -> List[WeaponDetection]:
        """
        Run weapon detection on a **cropped** image region.

        Returns
        -------
        list of (x1, y1, x2, y2, confidence, class_name)
            Coordinates are relative to the *crop*.
        """
        results = self.model.predict(
            source=crop,
            conf=conf,
            device=self.device,
            imgsz=self.imgsz,
            half=True,
            verbose=False,
        )

        detections: List[WeaponDetection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names.get(cls_id, str(cls_id))

                # Skip non-weapon / contextual classes
                if cls_name in IGNORED_CLASSES:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = round(float(box.conf[0]), 4)
                detections.append((x1, y1, x2, y2, confidence, cls_name))

        return detections

    # ── convenience: detect + remap to original frame ────────────────

    def detect_in_region(
        self,
        frame: np.ndarray,
        person_bbox: Tuple[int, int, int, int],
        conf: float = 0.3,
        pad_ratio: float = 0.10,
    ) -> List[WeaponDetection]:
        """
        Crop the person region from *frame* (with padding), run weapon
        detection, and **remap** box coordinates back to the full frame.

        Parameters
        ----------
        frame : np.ndarray
            The full camera frame (BGR).
        person_bbox : (x1, y1, x2, y2)
            Person bounding box in frame coordinates.
        conf : float
            Confidence threshold for the weapon model.
        pad_ratio : float
            Fraction of person-box width/height to add as padding
            (prevents cutting off weapons at the edges of the crop).

        Returns
        -------
        list of (x1, y1, x2, y2, confidence, class_name)
            Weapon boxes in **full-frame** coordinates.
        """
        h_frame, w_frame = frame.shape[:2]
        px1, py1, px2, py2 = person_bbox

        # ── apply padding ────────────────────────────────────────────
        pw = px2 - px1
        ph = py2 - py1
        pad_x = int(pw * pad_ratio)
        pad_y = int(ph * pad_ratio)

        cx1 = max(0, px1 - pad_x)
        cy1 = max(0, py1 - pad_y)
        cx2 = min(w_frame, px2 + pad_x)
        cy2 = min(h_frame, py2 + pad_y)

        crop = frame[cy1:cy2, cx1:cx2]

        if crop.size == 0:
            return []

        # ── resize crop to configured size for better small-object detection ─
        crop_h, crop_w = crop.shape[:2]
        target_size = int(self.imgsz)
        resized = cv2.resize(crop, (target_size, target_size))

        # Scale factors to map resized coords → original crop coords
        sx = crop_w / target_size
        sy = crop_h / target_size

        # ── detect on the resized crop ───────────────────────────────
        crop_dets = self.detect(resized, conf=conf)

        # ── remap: resized → original crop → full frame ─────────────
        remapped: List[WeaponDetection] = []
        for wx1, wy1, wx2, wy2, wconf, wname in crop_dets:
            remapped.append((
                int(wx1 * sx) + cx1,
                int(wy1 * sy) + cy1,
                int(wx2 * sx) + cx1,
                int(wy2 * sy) + cy1,
                wconf,
                wname,
            ))

        return remapped
