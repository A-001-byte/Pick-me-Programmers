import sys
import os

# Ensure project root is in python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
from core.pipeline import SurveillancePipeline

def main():
    """
    Main pipeline for Surveillance System.
    Continuously processes CCTV video streams.
    """
    print("Initializing Surveillance System...")
    pipeline = SurveillancePipeline()
    
    # Capture video from webcam using OpenCV
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Starting video stream analysis. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break
        
        # Process each frame through pipeline
        try:
            alerts = pipeline.process_frame(frame)
        except Exception as e:
            # Catching exceptions if modules are not fully implemented yet
            print(f"Pipeline error: {e}")
            alerts = []

        # Draw bounding boxes and alert information
        if alerts:
            for alert in alerts:
                # Handle both Event object and dict for flexibility
                if hasattr(alert, "to_dict"):
                    alert_data = alert.to_dict()
                elif isinstance(alert, dict):
                    alert_data = alert
                else:
                    continue
                    
                person_id = alert_data.get("person_id", "Unknown")
                bbox = alert_data.get("bbox", [])
                event_type = alert_data.get("event_type", "Unknown")
                risk_score = alert_data.get("risk_score", 0.0)
                
                # Show person ID, risk score, and event type
                text = f"ID: {person_id} | {event_type} | Risk: {risk_score:.2f}"
                
                # Bbox expected in format [x_min, y_min, x_max, y_max]
                if bbox and len(bbox) >= 4:
                    x1, y1, x2, y2 = map(int, bbox[:4])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, text, (x1, max(y1 - 10, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    # Generic display if no valid bbox is returned
                    cv2.putText(frame, text, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Display video feed
        cv2.imshow('Surveillance Feed', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()