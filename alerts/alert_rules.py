from typing import Dict, Any

class AlertRules:
    """Defines the rules that determine when an alert should be triggered."""
    
    def should_alert(self, decision: Dict[str, Any]) -> bool:
        """Returns True if the decision warrants an alert."""
        score = decision.get("risk_score", 0)
        behaviors = decision.get("behaviors", [])
        threat_level = decision.get("threat_level", "NORMAL").upper()
        
        # Immediate alert on weapon detection regardless of score
        if "weapon_detected" in behaviors:
            return True
        
        # Alert on zone intrusion
        if "zone_intrusion" in behaviors:
            return True
            
        # Alert on HIGH or CRITICAL threat level
        if threat_level in ("HIGH", "CRITICAL"):
            return True
            
        # Alert on score >= 50 (SUSPICIOUS level)
        if score >= 50:
            return True
        
        # Alert on persistent loitering (score >= 30 means recurrent)
        if "loitering" in behaviors and score >= 30:
            return True
            
        return False

    def get_alert_priority(self, decision: Dict[str, Any]) -> str:
        """Returns the priority level of the alert."""
        score = decision.get("risk_score", 0)
        behaviors = decision.get("behaviors", [])
        threat_level = decision.get("threat_level", "NORMAL").upper()
        
        if "weapon_detected" in behaviors or score >= 100 or threat_level == "CRITICAL":
            return "CRITICAL_ALARM"
        elif score >= 70 or threat_level == "HIGH":
            return "SECURITY_ALERT"
        elif score >= 50 or threat_level == "SUSPICIOUS":
            return "WARNING"
        elif "zone_intrusion" in behaviors:
            return "SECURITY_ALERT"
        else:
            return "INFO"
