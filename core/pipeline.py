"""
pipeline.py
───────────
Real-time surveillance pipeline for ThreatSense-AI.

Flow:
    webcam frame
        → YOLOv8x + ByteTrack  → tracked person bounding boxes (stable IDs)
        → for each person crop  → weapon detector → weapon boxes (remapped)
        → WeaponVerifier        → multi-frame confidence accumulation
                                   (confirmed only after ≥ 3 frames, avg conf ≥ 0.6)
        → BehaviorAnalyzer      → per-person behaviour signals
        → RiskEngine            → threat scoring and alert dispatch
        → visual overlay        → draw boxes / FPS counter
        → cv2.imshow
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional

import cv2
import numpy as np

from detection.person_detector import PersonDetector
from detection.weapon_detector import WeaponDetector
from weapon_verifier import WeaponVerifier
from core.stream_manager import stream_manager
from behavior.behavior_analyzer import BehaviorAnalyzer
from engine.risk_engine import RiskEngine

# ── Drawing constants ────────────────────────────────────────────────────────

COLOR_PERSON  = (0, 255, 0)       # green  — normal person
COLOR_ARMED   = (0, 0, 255)       # red    — armed person + weapon box
COLOR_WEAPON  = (0, 0, 255)       # red    — weapon bounding box
COLOR_FPS     = (0, 255, 255)     # yellow
COLOR_MEDIUM  = (0, 165, 255)     # orange — medium risk
COLOR_HIGH    = (0, 0, 255)       # red    — high/critical risk
FONT          = cv2.FONT_HERSHEY_SIMPLEX
THICKNESS     = 2

# Minimum weapon confidence to classify a person as armed
# Raised from 0.45 to 0.75 to reduce false positives
ARMED_CONF_THRESHOLD = 0.75

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
        person_model: str = "models/yolov8m.pt",
        weapon_model: Optional[str] = None,
        device: int | str | None = None,
        headless: bool = False,
        weapon_skip: int = 5,  # Run weapon detection every N frames
        risk_skip: int = 3,    # Run risk engine every N frames (reduces logging/CPU)
        imgsz: int = 416,      # Smaller size for faster processing (was 640)
    ) -> None:
        self.source = source
        self.person_conf = person_conf
        self.weapon_conf = weapon_conf
        self.armed_threshold = armed_threshold
        self.persist_frames = persist_frames
        self.device = device
        self.headless = headless
        
        # Validate skip parameters to prevent ZeroDivisionError in modulo operations
        if not isinstance(weapon_skip, int) or weapon_skip < 1:
            weapon_skip = 1
        if not isinstance(risk_skip, int) or risk_skip < 1:
            risk_skip = 1
        self.weapon_skip = weapon_skip
        self.risk_skip = risk_skip
        
        self.imgsz = imgsz
        self._frame_count = 0

        # Initialise detectors
        print(f"[pipeline] Loading person detector (ByteTrack) at {imgsz}px …")
        self.person_det = PersonDetector(
            model_path=person_model, device=device, imgsz=imgsz,
        )

        print(f"[pipeline] Loading weapon detector at {imgsz}px …")
        weapon_kwargs = {"device": device, "imgsz": imgsz}
        if weapon_model is not None:
            weapon_kwargs["model_path"] = weapon_model
        self.weapon_det = WeaponDetector(**weapon_kwargs)

        # ── WeaponVerifier: multi-frame confidence accumulation ────────────
        # Confirms a weapon only after ≥ 3 consistent detections with avg
        # confidence ≥ 0.6.  Resets evidence after 3 missed frames (decay).
        self.weapon_verifier = WeaponVerifier(
            min_frames=3,
            min_avg_conf=0.6,
            decay_after=3,
        )

        # ── BehaviorAnalyzer: per-person behaviour signals ─────────────────
        print("[pipeline] Initializing BehaviorAnalyzer …")
        self.behavior_analyzer = BehaviorAnalyzer()

        # ── RiskEngine: threat scoring and alert dispatch ──────────────────
        print("[pipeline] Initializing RiskEngine …")
        self.risk_engine = RiskEngine()

        # FPS tracking (rolling window of last 30 frames)
        self._fps_window: deque[float] = deque(maxlen=30)

        # Weapon buffer: track_id → {"weapons": [...], "ttl": int}
        # NOTE: used only for the *visual* overlay; behavioural flagging is
        # handled by WeaponVerifier + BehaviorAnalyzer (see run loop).
        self._weapon_buffer: dict[int, dict] = {}

        # Store risk decisions for drawing
        self._risk_decisions: dict[int, dict] = {}

    # ── main loop ────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the live surveillance loop.  Press **q** to quit."""
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open video source: {self.source}"
            )

        # Configure webcam for optimal FPS
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency

        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[pipeline] Webcam configured: {actual_w}x{actual_h} @ {actual_fps} FPS")

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

                # ── 2. Per-person weapon detection ───────────────────
                active_ids: set[int] = set()
                person_states: list[dict] = []

                # Collect all weapon detections across all persons this frame.
                # Also build the tracked-person list in the format expected by
                # WeaponVerifier and BehaviorAnalyzer.
                all_weapon_dets: list = []
                tracked_for_analyzer: list[dict] = []

                for px1, py1, px2, py2, pconf, tid in tracked:
                    active_ids.add(tid)
                    tracked_for_analyzer.append({
                        "id": tid,
                        "bbox": [px1, py1, px2, py2],
                    })

                    # Only run weapon detection every weapon_skip frames
                    should_detect = (self._frame_count % self.weapon_skip == 0)
                    
                    if should_detect:
                        weapons = self.weapon_det.detect_in_region(
                            frame,
                            (px1, py1, px2, py2),
                            conf=self.weapon_conf,
                        )
                        all_weapon_dets.extend(weapons)

                        # ── Visual display buffer (TTL-based) ───────────────
                        # Keep only weapons above the armed threshold for display.
                        high_conf = [
                            w for w in weapons if w[4] >= self.armed_threshold
                        ]
                        if high_conf:
                            self._weapon_buffer[tid] = {
                                "weapons": high_conf,
                                "ttl": self.persist_frames,
                            }
                    
                    # TTL decay happens on EVERY frame (not just detection frames)
                    # so persist_frames corresponds to actual frames, not detection cycles
                    if tid in self._weapon_buffer and not (should_detect and high_conf if should_detect else False):
                        self._weapon_buffer[tid]["ttl"] -= 1
                        if self._weapon_buffer[tid]["ttl"] <= 0:
                            del self._weapon_buffer[tid]

                    buffered = self._weapon_buffer.get(tid)
                    is_armed_display = buffered is not None
                    shown_weapons = buffered["weapons"] if buffered else []
                    
                    person_states.append({
                        "bbox": (px1, py1, px2, py2),
                        "conf": pconf,
                        "track_id": tid,
                        "armed": is_armed_display,
                        "weapons": shown_weapons,
                    })

                # Clean up display buffer for disappeared tracks
                vanished = [
                    tid for tid in self._weapon_buffer
                    if tid not in active_ids
                ]
                for tid in vanished:
                    del self._weapon_buffer[tid]

                # ── 3. WeaponVerifier — multi-frame confirmation ──────
                # Associates weapon bboxes to person bboxes via IoU and
                # accumulates frame counts + confidence scores.  A weapon is
                # confirmed only when frames >= 3 AND avg_conf >= 0.6.
                # Note: only update if we actually ran detection this frame.
                if self._frame_count % self.weapon_skip == 0:
                    confirmed_armed_ids = self.weapon_verifier.update(
                        all_weapon_dets, tracked_for_analyzer
                    )
                else:
                    # On skipped frames, get current confirmed IDs from verifier
                    confirmed_armed_ids = self.weapon_verifier.get_confirmed_ids()

                # ── 4. Propagate confirmed weapon flags to BehaviorAnalyzer
                for p in tracked_for_analyzer:
                    pid = p["id"]
                    self.behavior_analyzer.set_weapon_flag(
                        pid, pid in confirmed_armed_ids
                    )

                # ── 5. Behavior analysis ─────────────────────────────
                behavior_results = self.behavior_analyzer.analyze(
                    tracked_for_analyzer
                )

                # ── 6. Risk engine — threat scoring + alert dispatch ─
                # Process through risk engine (only every risk_skip frames to reduce CPU/logging)
                should_process_risk = (self._frame_count % self.risk_skip == 0)
                if behavior_results and should_process_risk:
                    risk_decisions = self.risk_engine.process_frame(behavior_results)
                    # Store decisions for drawing
                    for rd in risk_decisions:
                        self._risk_decisions[rd["person_id"]] = rd
                
                # Prune stale entries from _risk_decisions (track IDs no longer active)
                # This prevents cached decisions from being applied to recycled track IDs
                current_tids = {ps["track_id"] for ps in person_states}
                stale_tids = [tid for tid in self._risk_decisions if tid not in current_tids]
                for tid in stale_tids:
                    del self._risk_decisions[tid]
                
                # Update person_states with risk info
                for ps in person_states:
                    tid = ps["track_id"]
                    if tid in self._risk_decisions:
                        ps["risk_score"] = self._risk_decisions[tid].get("risk_score", 0)
                        ps["threat_level"] = self._risk_decisions[tid].get("threat_level", "low")
                    else:
                        ps["risk_score"] = 0
                        ps["threat_level"] = "low"

                # ── 7. Print confirmed weapon detections ─────────────
                for ps in person_states:
                    for wx1, wy1, wx2, wy2, wconf, wname in ps["weapons"]:
                        status = "CONFIRMED" if ps["track_id"] in confirmed_armed_ids else "unverified"
                        print(
                            f"ID {ps['track_id']} - {wname} [{status}]: "
                            f"[{wx1}, {wy1}, {wx2}, {wy2}, conf={wconf:.3f}]"
                        )

                # ── 8. Draw overlays ─────────────────────────────────
                self._draw(frame, person_states)

                # ── 9. FPS counter ───────────────────────────────────
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

                # ── 10. Push to Stream Manager ────────────────────────
                stream_manager.update_frame(frame)
                self._frame_count += 1

                # ── 11. Display ──────────────────────────────────────
                if not self.headless:
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
        Draw bounding boxes with track-ID labels and risk scores:
          • Low risk      → green box
          • Medium risk   → orange box
          • High risk     → red box
          • Armed person  → red box with "Armed" prefix
          • Weapon        → red box with weapon class name
        """
        for ps in person_states:
            x1, y1, x2, y2 = ps["bbox"]
            tid = ps["track_id"]
            threat_level = ps.get("threat_level", "low").lower()
            risk_score = ps.get("risk_score", 0)

            # Determine color based on threat level
            if ps["armed"] or threat_level in ("high", "critical"):
                color = COLOR_HIGH
            elif threat_level == "medium":
                color = COLOR_MEDIUM
            else:
                color = COLOR_PERSON

            # Build label
            if ps["armed"]:
                label = f"Armed ID {tid}"
            else:
                label = f"ID {tid}"
            
            # Add risk score to label if available
            if risk_score > 0:
                label += f" [{risk_score}]"

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
