class Config:
    """
    Core configuration settings for the ThreatSense-AI system.
    Handles environment variables, model paths, and stream URLs.
    """
    def __init__(self):
        self.yolo_model_path = "models/yolov8n.pt"
        self.weapon_model_path = "models/weapon_detector.pt"
        self.stream_url = 0  # Default webcam
        self.alert_threshold = 0.75
