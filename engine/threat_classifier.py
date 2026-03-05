from utils.config_loader import load_json_config
import os

class ThreatClassifier:
    """Classifies risk scores into threat levels based on configured thresholds."""
    
    def __init__(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "threat_levels.json")
        config = load_json_config(config_path)
        self.thresholds = config.get("thresholds", [])
        self.default_level = config.get("default_level", "CRITICAL")
        
        # Ensure thresholds are sorted by max value
        self.thresholds.sort(key=lambda x: x["max"])

    def classify(self, score: int) -> str:
        """Returns the threat level string for a given score."""
        for t in self.thresholds:
            if score <= t["max"]:
                return t["level"]
        return self.default_level
