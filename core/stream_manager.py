import threading
import cv2
import numpy as np

class StreamManager:
    """
    A thread-safe singleton to hold the latest frame from the surveillance pipeline.
    """
    _instance = None
    _lock = threading.Lock()
    
    # Default JPEG quality (0-100, higher = better quality, larger size)
    # Reduced to 65 for faster encoding while maintaining acceptable quality
    DEFAULT_JPEG_QUALITY = 65

    def __init__(self):
        # Already initialized by __new__ for the singleton, but we can guard it
        if not hasattr(self, 'initialized'):
            self.frame = None
            self.lock = threading.Lock()
            self.jpeg_quality = self.DEFAULT_JPEG_QUALITY
            self.initialized = True

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StreamManager, cls).__new__(cls)
        return cls._instance

    def update_frame(self, frame: np.ndarray):
        """Update the latest frame. Stores reference directly for speed."""
        if frame is None:
            return
        with self.lock:
            # Store directly instead of copying - pipeline owns the frame lifecycle
            self.frame = frame

    def get_frame_bytes(self):
        """Encode the current frame as JPEG and return bytes."""
        with self.lock:
            if self.frame is None:
                return None
            
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            success, buffer = cv2.imencode('.jpg', self.frame, encode_params)
            if not success:
                return None
            
            return buffer.tobytes()

stream_manager = StreamManager()
