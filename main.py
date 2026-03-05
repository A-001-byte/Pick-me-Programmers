"""
ThreatSense-AI — Risk Engine Main Pipeline
============================================
Simulates a real-time surveillance feed by sending tracked-person data
through the Risk Engine decision layer.

Usage:
    python main.py
"""

import json
import time
from engine.risk_engine import RiskEngine
from risk_logging.event_logger import EventLogger

logger = EventLogger("MainPipeline")

def main():
    logger.info("ThreatSense-AI Risk Engine starting up...")
    
    engine = RiskEngine()
    
    # ---------------------------------------------------------------
    # Simulated frames from tracking pipeline (Members 1 & 2 output)
    # Each frame is a list of tracked persons in that moment
    # ---------------------------------------------------------------
    simulated_frames = [
        # Frame 1: Two people, minor activity
        [
            {"id": 1, "bbox": [100, 200, 180, 350], "speed": 1.2, "loitering": True,  "zone_intrusion": False, "weapon_detected": False},
            {"id": 2, "bbox": [300, 120, 380, 330], "speed": 0.5, "loitering": False, "zone_intrusion": False, "weapon_detected": False},
        ],
        # Frame 2: Person 1 continues loitering, Person 2 enters restricted zone
        [
            {"id": 1, "bbox": [105, 205, 185, 355], "speed": 0.8, "loitering": True,  "zone_intrusion": False, "weapon_detected": False},
            {"id": 2, "bbox": [310, 130, 390, 340], "speed": 2.8, "loitering": False, "zone_intrusion": True,  "weapon_detected": False},
        ],
        # Frame 3: Person 1 now intrudes zone (escalation!), Person 3 appears with weapon
        [
            {"id": 1, "bbox": [110, 210, 190, 360], "speed": 3.5, "loitering": True,  "zone_intrusion": True,  "weapon_detected": False},
            {"id": 3, "bbox": [500, 100, 580, 300], "speed": 0.2, "loitering": False, "zone_intrusion": True,  "weapon_detected": True},
        ],
        # Frame 4: All calm — demonstrates decay
        [
            {"id": 1, "bbox": [115, 215, 195, 365], "speed": 0.3, "loitering": False, "zone_intrusion": False, "weapon_detected": False},
            {"id": 2, "bbox": [320, 140, 400, 350], "speed": 0.4, "loitering": False, "zone_intrusion": False, "weapon_detected": False},
        ],
    ]
    
    for frame_idx, frame in enumerate(simulated_frames):
        print(f"\n{'='*60}")
        logger.info(f"Processing Frame {frame_idx + 1} — {len(frame)} person(s) detected")
        print(f"{'='*60}")
        
        results = engine.process_frame(frame)
        
        for r in results:
            print(f"\n  Person {r['person_id']}:")
            print(f"    Score  : {r['risk_score']}")
            print(f"    Level  : {r['threat_level']}")
            print(f"    Reasons:")
            for reason in r["reasons"]:
                print(f"      - {reason}")
        
        # Simulate small time gap between frames
        time.sleep(0.5)
    
    logger.info("Pipeline simulation complete.")

if __name__ == "__main__":
    main()
