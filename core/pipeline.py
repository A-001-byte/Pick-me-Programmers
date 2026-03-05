import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detection.detector import detect_people
from tracking.tracker import track_people
from behavior.analyzer import analyze_behavior
from risk_engine.risk import compute_risk
from alerts.manager import generate_alerts


class SurveillancePipeline:
    def __init__(self):
        pass

    def process_frame(self, frame):
        # Determine the detections in the frame
        try:
            detections = detect_people(frame)
        except Exception:
            detections = []

        # Track the detected people
        try:
            tracks = track_people(detections)
        except Exception:
            tracks = detections

        # Analyze the behavior of tracked people
        try:
            behaviors = analyze_behavior(tracks)
        except Exception:
            behaviors = tracks

        # Compute the risk based on the analyzed behavior
        try:
            risks = compute_risk(behaviors)
        except Exception:
            risks = behaviors

        # Generate alerts based on the computed risk
        try:
            alerts = generate_alerts(risks)
        except Exception:
            alerts = []

        return alerts