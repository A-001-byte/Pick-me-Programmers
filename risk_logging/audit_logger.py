import json
import os
from datetime import datetime
from typing import List

class AuditLogger:
    """Specialized logger for recording immutable security decisions and explanations."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        self.log_file = os.path.join(self.log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl")
        
    def log_decision(self, person_id: int, behaviors: list, risk_score: int, threat_level: str, reasons: list):
        """Logs a standardized JSON entry for a risk decision."""
        entry = {
            "person_id": person_id,
            "behaviors": behaviors,
            "risk_score": risk_score,
            "threat_level": threat_level,
            "reasons": reasons,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Log to file (console printing removed to avoid log flooding)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
