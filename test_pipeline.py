"""
ThreatSense-AI – Automated Pipeline Test Suite.

Simulates detections across multiple frames and validates:
  1. ID Persistence
  2. Speed Calculation
  3. Loitering Detection
  4. Zone Intrusion Detection
  5. Weapon Flag Propagation
  6. Crowd Density Alert

Run:  python test_pipeline.py
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracking.sort_tracker import SortTracker
from tracking.sort_algorithm import KalmanBoxTracker
from behavior.behavior_analyzer import BehaviorAnalyzer

passed = 0
failed = 0


def report(name, ok, detail=""):
    global passed, failed
    tag = "PASS" if ok else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"[{tag}] {name}{suffix}")
    if ok:
        passed += 1
    else:
        failed += 1


# ---- helpers ---------------------------------------------------------------

def feed_constant_detection(tracker, bbox, n_frames):
    """Feed the same bbox for n_frames and return last result."""
    result = []
    for _ in range(n_frames):
        result = tracker.update([bbox])
    return result


# ---- Test 1: ID Persistence -----------------------------------------------

def test_id_persistence():
    """Same detection fed over many frames should keep the same track ID."""
    # Reset ID counter so the test is deterministic
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=3, iou_threshold=0.3)
    bbox = [100, 100, 200, 300, 0.9]

    ids_seen = set()
    for _ in range(10):
        result = tracker.update([bbox])
        for obj in result:
            ids_seen.add(obj["id"])

    # After enough frames, we should have a single consistent ID
    ok = len(ids_seen) == 1
    report("ID Persistence", ok, f"unique IDs = {ids_seen}")


# ---- Test 2: Speed Calculation ---------------------------------------------

def test_speed_calculation():
    """Moving bbox should produce non-zero speed."""
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)
    analyzer = BehaviorAnalyzer()

    # Feed an initial position for several frames to establish the track
    for _ in range(5):
        tracked = tracker.update([[100, 100, 200, 300, 0.9]])

    # Now move the box significantly
    tracked = tracker.update([[150, 150, 250, 350, 0.9]])
    behaviours = analyzer.analyze(tracked)

    # Feed the original position first to build history
    # Reset analyzer too
    analyzer2 = BehaviorAnalyzer()
    KalmanBoxTracker._id_counter = 0
    tracker2 = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)

    # Position A for a few frames
    for _ in range(4):
        t = tracker2.update([[100, 100, 200, 300, 0.9]])
        analyzer2.analyze(t)

    # Position B (shifted)
    t = tracker2.update([[130, 140, 230, 340, 0.9]])
    results = analyzer2.analyze(t)

    if results:
        speed = results[0]["speed"]
        ok = speed > 0
        report("Speed Calculation", ok, f"speed = {speed}")
    else:
        report("Speed Calculation", False, "no tracked objects returned")


# ---- Test 3: Loitering Detection -------------------------------------------

def test_loitering():
    """A stationary person should be flagged as loitering after enough frames."""
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)
    analyzer = BehaviorAnalyzer(loiter_threshold=40, loiter_frames=30)

    bbox = [100, 100, 200, 300, 0.9]
    results = []
    for _ in range(35):
        tracked = tracker.update([bbox])
        results = analyzer.analyze(tracked)

    if results:
        ok = results[0]["loitering"] is True
        report("Loitering Detection", ok, f"loitering = {results[0]['loitering']}")
    else:
        report("Loitering Detection", False, "no tracked objects returned")


# ---- Test 4: Zone Intrusion -----------------------------------------------

def test_zone_intrusion():
    """Person inside restricted zone should trigger zone_intrusion flag."""
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)
    analyzer = BehaviorAnalyzer()
    analyzer.set_zones([[50, 50, 250, 350]])  # zone covering the bbox

    bbox = [100, 100, 200, 300, 0.9]
    results = []
    for _ in range(5):
        tracked = tracker.update([bbox])
        results = analyzer.analyze(tracked)

    if results:
        ok = results[0]["zone_intrusion"] is True
        report("Zone Intrusion", ok, f"zone_intrusion = {results[0]['zone_intrusion']}")
    else:
        report("Zone Intrusion", False, "no tracked objects returned")


# ---- Test 5: Weapon Flag --------------------------------------------------

def test_weapon_flag():
    """set_weapon_flag should propagate into analyse output."""
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)
    analyzer = BehaviorAnalyzer()

    bbox = [100, 100, 200, 300, 0.9]
    results = []
    for _ in range(5):
        tracked = tracker.update([bbox])
        results = analyzer.analyze(tracked)

    # Flag the person
    if results:
        pid = results[0]["id"]
        analyzer.set_weapon_flag(pid, True)
        tracked = tracker.update([bbox])
        results = analyzer.analyze(tracked)
        ok = results[0]["weapon_detected"] is True
        report("Weapon Flag", ok, f"weapon_detected = {results[0]['weapon_detected']}")
    else:
        report("Weapon Flag", False, "no tracked objects returned")


# ---- Test 6: Crowd Density Alert -------------------------------------------

def test_crowd_density():
    """5+ persons tracked simultaneously should trigger crowd_density_alert."""
    KalmanBoxTracker._id_counter = 0
    tracker = SortTracker(max_age=30, min_hits=1, iou_threshold=0.3)
    analyzer = BehaviorAnalyzer(crowd_threshold=5)

    # Five non-overlapping boxes
    detections = [
        [10, 10, 60, 160, 0.9],
        [70, 10, 130, 160, 0.9],
        [140, 10, 200, 160, 0.9],
        [210, 10, 270, 160, 0.9],
        [280, 10, 340, 160, 0.9],
    ]

    results = []
    for _ in range(5):
        tracked = tracker.update(detections)
        results = analyzer.analyze(tracked)

    if results:
        ok = all(r["crowd_density_alert"] for r in results)
        alerts = [r["crowd_density_alert"] for r in results]
        report("Crowd Density Alert", ok, f"alerts = {alerts}")
    else:
        report("Crowd Density Alert", False, "no tracked objects returned")


# ---- Run all tests ---------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  ThreatSense-AI  –  Pipeline Test Suite")
    print("=" * 60)
    print()

    test_id_persistence()
    test_speed_calculation()
    test_loitering()
    test_zone_intrusion()
    test_weapon_flag()
    test_crowd_density()

    print()
    print("-" * 60)
    print(f"  Results:  {passed} passed,  {failed} failed")
    print("-" * 60)

    sys.exit(0 if failed == 0 else 1)
