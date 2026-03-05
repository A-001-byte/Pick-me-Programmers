"""
pipeline.py
───────────
Real-time surveillance pipeline that chains a person detector (with
ByteTrack tracking) with a weapon detector running on each person crop.

Flow:
    webcam frame
        → YOLOv8x + ByteTrack → tracked person bounding boxes (stable IDs)
        → for each person crop → weapon detector → weapon boxes (remapped)
        → temporal weapon buffer (persist label for N frames per track ID)
        → draw overlays + FPS counter
        → cv2.imshow
"""

from __future__ import annotations

import sys
import os
import time
from collections import deque
from typing import Optional

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np

from detection.person_detector import PersonDetector
from detection.weapon_detector import WeaponDetector

# ── Drawing constants ────────────────────────────────────────────────────────

COLOR_PERSON  = (0, 255, 0)       # green  — normal person
COLOR_ARMED   = (0, 0, 255)       # red    — armed person + weapon box
COLOR_WEAPON  = (0, 0, 255)       # red    — weapon bounding box
COLOR_FPS     = (0, 255, 255)     # yellow
FONT          = cv2.FONT_HERSHEY_SIMPLEX
THICKNESS     = 2

# Minimum weapon confidence to classify a person as armed
ARMED_CONF_THRESHOLD = 0.45

# How many frames to keep showing "Armed Person" after the last detection
WEAPON_PERSIST_FRAMES = 5


class SurveillancePipeline:
    """Orchestrate person tracking + weapon detection on a live source."""

    def __init__(
        self,
        source: int | str = 0,
        person_conf: float = 0.4,
        weapon_conf: float = 0.3,
        armed_threshold: float = ARMED_CONF_THRESHOLD,
        persist_frames: int = WEAPON_PERSIST_FRAMES,
        person_model: str = "yolov8x.pt",
        weapon_model: Optional[str] = None,
        device: int | str = 0,
    ) -> None:
        self.source = source
        self.person_conf = person_conf
        self.weapon_conf = weapon_conf
        self.armed_threshold = armed_threshold
        self.persist_frames = persist_frames
        self.device = device

        # Initialise detectors
        print("[pipeline] Loading person detector (ByteTrack) …")
        self.person_det = PersonDetector(
            model_path=person_model, device=device,
        )

        print("[pipeline] Loading weapon detector …")
        weapon_kwargs = {"device": device}
        if weapon_model is not None:
            weapon_kwargs["model_path"] = weapon_model
        self.weapon_det = WeaponDetector(**weapon_kwargs)

        # FPS tracking (rolling window of last 30 frames)
        self._fps_window: deque[float] = deque(maxlen=30)

        # Weapon buffer: track_id → {"weapons": [...], "ttl": int}
        self._weapon_buffer: dict[int, dict] = {}

    # ── main loop ────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the live surveillance loop.  Press **q** to quit."""
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open video source: {self.source}"
            )

        print(f"[pipeline] Streaming from source={self.source}  "
              f"(press 'q' to quit)")

        try:
            while True:
                t0 = time.perf_counter()

                ret, frame = cap.read()
                if not ret:
                    print("[pipeline] End of stream.")
                    break

                # ── 1. Detect + track persons (ByteTrack) ────────────
                tracked = self.person_det.track(
                    frame, conf=self.person_conf,
                )

                # ── 2. Per-person weapon detection + buffer ──────────
                active_ids: set[int] = set()
                person_states: list[dict] = []

                for px1, py1, px2, py2, pconf, tid in tracked:
                    active_ids.add(tid)

                    weapons = self.weapon_det.detect_in_region(
                        frame,
                        (px1, py1, px2, py2),
                        conf=self.weapon_conf,
                    )

                    # Keep only weapons above the armed threshold
                    high_conf = [
                        w for w in weapons if w[4] >= self.armed_threshold
                    ]

                    if high_conf:
                        # Fresh detection → refresh buffer
                        self._weapon_buffer[tid] = {
                            "weapons": high_conf,
                            "ttl": self.persist_frames,
                        }
                    elif tid in self._weapon_buffer:
                        # No detection this frame → decrement TTL
                        self._weapon_buffer[tid]["ttl"] -= 1
                        if self._weapon_buffer[tid]["ttl"] <= 0:
                            del self._weapon_buffer[tid]

                    # Determine armed state from buffer
                    buffered = self._weapon_buffer.get(tid)
                    is_armed = buffered is not None
                    shown_weapons = buffered["weapons"] if buffered else []

                    person_states.append({
                        "bbox": (px1, py1, px2, py2),
                        "conf": pconf,
                        "track_id": tid,
                        "armed": is_armed,
                        "weapons": shown_weapons,
                    })

                # Clean up buffer for tracks that disappeared
                vanished = [
                    tid for tid in self._weapon_buffer
                    if tid not in active_ids
                ]
                for tid in vanished:
                    del self._weapon_buffer[tid]

                # ── 3. Print weapon detections ───────────────────────
                for ps in person_states:
                    for wx1, wy1, wx2, wy2, wconf, wname in ps["weapons"]:
                        print(
                            f"ID {ps['track_id']} - {wname}: "
                            f"[{wx1}, {wy1}, {wx2}, {wy2}, {wconf}]"
                        )

                # ── 4. Draw overlays ─────────────────────────────────
                self._draw(frame, person_states)

                # ── 5. FPS counter ───────────────────────────────────
                elapsed = time.perf_counter() - t0
                self._fps_window.append(elapsed)
                fps = len(self._fps_window) / sum(self._fps_window)
                cv2.putText(
                    frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    FONT,
                    1.0,
                    COLOR_FPS,
                    2,
                )

                # ── 6. Display ───────────────────────────────────────
                cv2.imshow("ThreatSense-AI", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[pipeline] Stopped.")

    # ── drawing helpers ──────────────────────────────────────────────

    @staticmethod
    def _draw(
        frame: np.ndarray,
        person_states: list[dict],
    ) -> None:
        """
        Draw bounding boxes with track-ID labels:
          • Normal person  → green box, "Person ID X"
          • Armed person   → red box,   "Armed Person ID X"
          • Weapon         → red box with weapon class name
        """
        for ps in person_states:
            x1, y1, x2, y2 = ps["bbox"]
            tid = ps["track_id"]

            if ps["armed"]:
                color = COLOR_ARMED
                label = f"Armed Person ID {tid}"
            else:
                color = COLOR_PERSON
                label = f"Person ID {tid}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, THICKNESS)
            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 8, 0)),
                FONT,
                0.6,
                color,
                1,
            )

            # Weapon boxes
            for wx1, wy1, wx2, wy2, wconf, wname in ps["weapons"]:
                cv2.rectangle(
                    frame, (wx1, wy1), (wx2, wy2), COLOR_WEAPON, THICKNESS,
                )
                cv2.putText(
                    frame,
                    f"{wname} {wconf:.2f}",
                    (wx1, max(wy1 - 8, 0)),
                    FONT,
                    0.6,
                    COLOR_WEAPON,
                    1,
                )
