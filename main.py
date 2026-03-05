"""
main.py
───────
Entry point for the ThreatSense-AI real-time surveillance system.

Usage:
    python main.py                           # webcam (default)
    python main.py --source rtsp://...       # RTSP stream
    python main.py --source video.mp4        # video file
    python main.py --person-conf 0.5 --weapon-conf 0.4
"""

from __future__ import annotations

import sys
import os
import argparse

# Ensure project root is in python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline import SurveillancePipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="ThreatSense-AI — real-time weapon surveillance",
    )
    p.add_argument(
        "--source",
        default="0",
        help="Video source: webcam index (0), file path, or RTSP URL "
             "(default: 0)",
    )
    p.add_argument(
        "--person-conf",
        type=float,
        default=0.4,
        help="Person detection confidence threshold (default: 0.4)",
    )
    p.add_argument(
        "--weapon-conf",
        type=float,
        default=0.3,
        help="Weapon detection confidence threshold (default: 0.3)",
    )
    p.add_argument(
        "--person-model",
        default="yolov8x.pt",
        help="Path to the person detector model (default: yolov8x.pt)",
    )
    p.add_argument(
        "--weapon-model",
        default=None,
        help="Path to the weapon detector model "
             "(default: models/weapon_detector.pt)",
    )
    p.add_argument(
        "--armed-threshold",
        type=float,
        default=0.65,
        help="Min weapon confidence to label person as armed (default: 0.65)",
    )
    p.add_argument(
        "--device",
        default="0",
        help="Inference device: GPU index or 'cpu' (default: 0)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Allow bare integer for webcam index
    source = int(args.source) if args.source.isdigit() else args.source

    pipeline = SurveillancePipeline(
        source=source,
        person_conf=args.person_conf,
        weapon_conf=args.weapon_conf,
        armed_threshold=args.armed_threshold,
        person_model=args.person_model,
        weapon_model=args.weapon_model,
        device=int(args.device) if args.device.isdigit() else args.device,
    )

    print("╔══════════════════════════════════════╗")
    print("║     ThreatSense-AI  •  Surveillance  ║")
    print("╚══════════════════════════════════════╝")
    pipeline.run()


if __name__ == "__main__":
    main()