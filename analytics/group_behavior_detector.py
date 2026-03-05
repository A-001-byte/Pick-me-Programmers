from typing import List, Dict, Any

class GroupBehaviorDetector:
    """Detects coordinated suspicious behavior across multiple people."""
    
    def detect_group_threats(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyzes current decisions for group-level threats."""
        group_alerts = []
        
        # Pattern 1: Coordinated loitering (3+ people)
        loitering_ids = [d["person_id"] for d in decisions if "loitering" in d.get("behaviors", [])]
        if len(loitering_ids) >= 3:
            group_alerts.append({
                "type": "GROUP_LOITERING",
                "members": loitering_ids,
                "description": f"Coordinated loitering detected involving {len(loitering_ids)} people"
            })
            
        # Pattern 2: Simultaneous Intrusions
        intruders = [d["person_id"] for d in decisions if d["risk_score"] >= 70]
        if len(intruders) >= 2:
           group_alerts.append({
                "type": "MASS_INCURSION",
                "members": intruders,
                "description": "Multiple high-risk movements detected simultaneously"
            })
            
        return group_alerts
