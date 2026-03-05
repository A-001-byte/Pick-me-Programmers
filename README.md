# ThreatSense-AI

A production-level computer vision system for analyzing CCTV video streams.

## Features

1. Person detection using YOLOv8
2. Weapon detection using a custom trained model
3. Multi-object tracking using ByteTrack
4. Behavior analysis (motion patterns, zone intrusion, crowd density)
5. Threat scoring engine
6. Alert generation
7. Flask backend for logging events
8. Web dashboard for visualization

## Project Structure
- `datasets/`: Training and validation datasets.
- `models/`: Pre-trained and custom models.
- `training/`: Model training scripts.
- `core/`: Core configurations and types.
- `detection/`: Object detection modules.
- `tracking/`: Multi-object tracking modules.
- `behavior/`: Behavior analysis and heuristics.
- `risk_engine/`: Threat scoring logic.
- `alerts/`: Alert generation and notification system.
- `backend/`: Flask-based API for logging.
- `dashboard/`: Web visualization dashboard.
- `utils/`: Common utilities and helpers.
