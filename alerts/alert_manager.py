from typing import Dict, Any, List, Optional
from alerts.alert_rules import AlertRules
from utils.time_utils import get_current_timestamp_str

class AlertManager:
    """Manages the generation and dispatch of security alerts."""
    
    def __init__(self):
        self.rules = AlertRules()
        self.alert_log: List[Dict[str, Any]] = []

    def evaluate_and_alert(self, decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Checks a decision against alert rules and generates an alert if warranted."""
        if not self.rules.should_alert(decision):
            return None
            
        priority = self.rules.get_alert_priority(decision)
        
        alert = {
            "person_id": decision["person_id"],
            "risk_score": decision["risk_score"],
            "threat_level": decision["threat_level"],
            "priority": priority,
            "reasons": decision.get("reasons", []),
            "timestamp": get_current_timestamp_str()
        }
        
        self.alert_log.append(alert)
        
        # In production, this would send to a message queue, webhook, or dashboard
        print(f"\n{'='*60}")
        print(f"  *** {priority} ***")
        print(f"  Person ID : {alert['person_id']}")
        print(f"  Score     : {alert['risk_score']}")
        print(f"  Level     : {alert['threat_level']}")
        print(f"  Reasons   :")
        for r in alert["reasons"]:
            print(f"    - {r}")
        print(f"{'='*60}\n")
        
        return alert

    def evaluate_group_alerts(self, group_alerts: List[Dict[str, Any]]):
        """Handles group-level alerts from the GroupBehaviorDetector."""
        for ga in group_alerts:
            print(f"\n{'#'*60}")
            print(f"  *** GROUP THREAT: {ga['type']} ***")
            print(f"  Members   : {ga['members']}")
            print(f"  Details   : {ga['description']}")
            print(f"{'#'*60}\n")
