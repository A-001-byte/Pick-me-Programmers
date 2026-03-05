class PersonDetector:
    """
    Person detection module using YOLOv8.
    Responsible for identifying individuals in a frame.
    """
    def __init__(self):
        # self.model = YOLO('yolov8n.pt')
        pass

    def detect(self, frame):
        """Returns bounding boxes and confidences for detected persons."""
        return []

class WeaponDetector:
    """
    Custom trained weapon detection module.
    Responsible for identifying firearms, knives, etc.
    """
    def __init__(self):
        pass

    def detect(self, frame):
        """Returns bounding boxes and confidences for detected weapons."""
        return []
