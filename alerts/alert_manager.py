from typing import Dict, Any, List, Optional
import logging
import time
from alerts.alert_rules import AlertRules
from utils.time_utils import get_current_timestamp_str

logger = logging.getLogger(__name__)

# Import database persistence functions
try:
    from backend.database import add_alert as db_add_alert, add_incident as db_add_incident
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    db_add_alert = None
    db_add_incident = None


def normalize_risk_score(raw_score: float) -> float:
    """Normalize risk score to 0.0-1.0 range.
    
    Handles both percentage (0-100) and fractional (0.0-1.0) inputs.
    Returns clamped value in [0.0, 1.0].
    """
    if raw_score > 1.0:
        # Assume percentage, convert to fraction
        score = raw_score / 100.0
    else:
        score = raw_score
    # Clamp to valid range
    return max(0.0, min(1.0, score))


class AlertManager:
    """Manages the generation and dispatch of security alerts."""
    
    # Throttle settings: max 1 alert per person per behavior per N seconds
    THROTTLE_WINDOW_SECONDS = 30
    
    def __init__(self, camera_id: str = "CAM-01"):
        self.rules = AlertRules()
        self.alert_log: List[Dict[str, Any]] = []
        self.camera_id = camera_id
        # Throttle tracking: key = (person_id, behavior_key) -> last_alert_time
        self._throttle_cache: Dict[tuple, float] = {}

    def _get_throttle_key(self, decision: Dict[str, Any]) -> tuple:
        """Generate a throttle key from person_id and behavior set.
        
        Uses an order-independent representation of behaviors (sorted tuple)
        so identical behavior sets in different orders yield the same key.
        """
        person_id = decision.get("person_id", "unknown")
        behaviors = decision.get("behaviors", [])
        # Normalize: deduplicate via set, sort for consistency, convert to tuple
        behavior_key = tuple(sorted(set(behaviors))) if behaviors else ("general",)
        return (person_id, behavior_key)

    def _is_throttled(self, decision: Dict[str, Any]) -> bool:
        """Check if this alert should be throttled."""
        key = self._get_throttle_key(decision)
        now = time.time()
        
        if key in self._throttle_cache:
            last_time = self._throttle_cache[key]
            if now - last_time < self.THROTTLE_WINDOW_SECONDS:
                return True
        
        # Update throttle cache
        self._throttle_cache[key] = now
        
        # Cleanup old entries (older than 2x throttle window)
        cutoff = now - (self.THROTTLE_WINDOW_SECONDS * 2)
        self._throttle_cache = {k: v for k, v in self._throttle_cache.items() if v > cutoff}
        
        return False

    def evaluate_and_alert(self, decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Checks a decision against alert rules and generates an alert if warranted."""
        if not self.rules.should_alert(decision):
            return None
        
        # Apply throttling to prevent alert spam
        if self._is_throttled(decision):
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
        
        # Persist to database if available
        if DB_AVAILABLE and db_add_alert is not None:
            try:
                # Determine event_type from behaviors or reasons
                behaviors = decision.get("behaviors", [])
                if "weapon_detected" in behaviors:
                    event_type = "Weapon Detected"
                elif "zone_intrusion" in behaviors:
                    event_type = "Zone Intrusion"
                elif "loitering" in behaviors:
                    event_type = "Loitering Detected"
                elif behaviors:
                    event_type = behaviors[0].replace("_", " ").title()
                else:
                    event_type = "Suspicious Behavior"
                
                # Normalize risk_score to 0.0-1.0 range
                risk_score = normalize_risk_score(decision["risk_score"])
                
                db_add_alert(
                    person_id=str(decision["person_id"]),
                    event_type=event_type,
                    risk_score=risk_score,
                    risk_level=decision["threat_level"].lower(),
                    camera_id=self.camera_id
                )

                # Promote high-priority detections to incidents
                if db_add_incident is not None and decision["threat_level"].lower() in ("high", "critical"):
                    db_add_incident(
                        title=f"{event_type}: ID {decision['person_id']}",
                        description=f"Automated incident for {decision['person_id']}. Reasons: {', '.join(decision.get('reasons', []))}",
                        event_type=event_type,
                        location="Main Entrance",  # Could be dynamic if configured
                        risk_level=decision["threat_level"].lower(),
                        status="open"
                    )
            except Exception:
                logger.exception("Failed to persist alert/incident to DB")
        
        # Console output for debugging
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
