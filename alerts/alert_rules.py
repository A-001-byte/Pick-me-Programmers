from typing import Dict, Any

class AlertRules:
    """Defines the rules that determine when an alert should be triggered."""
    
    def should_alert(self, decision: Dict[str, Any]) -> bool:
        """Returns True if the decision warrants an alert."""
        score = decision.get("risk_score", 0)
        behaviors = decision.get("behaviors", [])
        
        # Immediate alert on weapon detection regardless of score
        if "weapon_detected" in behaviors:
            return True
            
        # Alert on HIGH_RISK or above
        if score >= 70:
            return True
            
        return False

    def get_alert_priority(self, decision: Dict[str, Any]) -> str:
        """Returns the priority level of the alert."""
        score = decision.get("risk_score", 0)
        behaviors = decision.get("behaviors", [])
        
        if "weapon_detected" in behaviors or score >= 100:
            return "CRITICAL_ALARM"
        elif score >= 70:
            return "SECURITY_ALERT"
        else:
            return "INFO"
