from typing import List
from memory.person_memory import PersonMemory

class PatternDetector:
    """Detects suspicious sequences of behaviors over time."""
    
    def detect_patterns(self, person_id: int, memory: PersonMemory) -> List[str]:
        """Analyzes behavior history for suspicious patterns."""
        alerts = []
        
        # Pattern 1: Escalation Pattern (multiple intrusions within short time)
        if memory.zone_intrusions >= 2:
            alerts.append("Pattern Detected: Multiple zone intrusions in a single session")
            
        # Pattern 2: Persistent Suspicion (History of high scores)
        high_risk_phases = [score for score in memory.risk_history if score >= 60]
        if len(high_risk_phases) >= 3:
            alerts.append("Pattern Detected: Persistent high-risk behavior history")
            
        # Pattern 3: Loitering to Intrusion escalation (Simulated)
        if memory.loiter_count >= 1 and memory.zone_intrusions >= 1:
            alerts.append("Pattern Detected: Loitering preceding zone intrusion")
            
        return alerts
