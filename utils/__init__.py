class Logger:
    """
    Standardizes logging across the ThreatSense-AI application.
    """
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")

def draw_bounding_boxes(frame, detections):
    """Utility to draw bounding boxes on an image frame."""
    pass
