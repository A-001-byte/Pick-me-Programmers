from typing import List, Tuple

class BehaviorFusion:
    """
    Applies logic to combine multiple behaviors into complex risk signals.
    Implements aggressive scoring for specific behavior combinations.
    """
    
    def apply_fusion(self, behaviors: List[str], base_score: int) -> Tuple[int, List[str]]:
        """
        Calculates extra risk based on behavior combinations.
        Returns (bonus_score, reasons).
        """
        bonus = 0
        reasons = []
        
        # loitering + zone_intrusion → extra risk
        if "loitering" in behaviors and "zone_intrusion" in behaviors:
            bonus += 15
            reasons.append("Synergy: Loitering combined with zone intrusion")
            
        # zone_intrusion + weapon_detected → CRITICAL (ensure score >= 100)
        if "zone_intrusion" in behaviors and "weapon_detected" in behaviors:
            if base_score + bonus < 100:
                bonus = 100 - base_score
            reasons.append("Synergy: Critical weapon detection in restricted zone")
            
        return bonus, reasons
