"""
train_weapon_detector.py
────────────────────────
YOLOv8m training script for weapon detection using the merged dataset.

Optimised for small-object detection with:
  • 960 px input resolution
  • AdamW optimizer
  • Early stopping (patience = 10 epochs on val mAP)
  • Mixed-precision (AMP) training

Usage:
    python training/train_weapon_detector.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from ultralytics import YOLO

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_YAML    = PROJECT_ROOT / "datasets" / "weapon_merged" / "data.yaml"
SAVE_DIR     = PROJECT_ROOT / "runs" / "detect" / "weapon_training"

# ── Training ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train weapon detection model.")
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device to train on (e.g., '0' for GPU 0, 'cpu', or 'auto')."
    )
    args = parser.parse_args()

    # Pre-flight check
    if not DATA_YAML.exists():
        sys.exit(f"❌ Error: Dataset config {DATA_YAML} not found. Please run the merge script first.")

    # Load YOLOv8m with COCO pretrained weights
    model = YOLO("yolov8m.pt")

    # Train with settings optimised for small-object weapon detection
    device_arg = int(args.device) if args.device.isdigit() else args.device

    model.train(
        data        = str(DATA_YAML),
        imgsz       = 960,
        epochs      = 40,
        batch       = 8,
        device      = device_arg,
        workers     = 4,
        amp         = True,
        optimizer   = "AdamW",
        cache       = "disk",
        patience    = 10,          # early stopping on val mAP
        project     = str(SAVE_DIR.parent),
        name        = SAVE_DIR.name,
        exist_ok    = True,
        verbose     = True,
    )

    print(f"\n✅ Training complete — results saved to {SAVE_DIR}")


if __name__ == "__main__":
    main()
