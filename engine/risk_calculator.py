from typing import List, Dict, Tuple
from utils.config_loader import load_json_config
from memory.person_memory import PersonMemory
import os

class RiskCalculator:
    """Computes the baseline risk score for a person."""
    
    def __init__(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "risk_weights.json")
        self.weights = load_json_config(config_path)
        
    def compute_score(self, behaviors: Dict[str, bool], memory: PersonMemory) -> Tuple[int, List[str], List[str]]:
        """
        Computes the base score and provides explanations.
        Increases risk faster if there is historical suspicious activity.
        """
        score = 0
        reasons = []
        
        # 1. Base weights for current behaviors
        active_behaviors = []
        for behavior, active in behaviors.items():
            if active:
                weight = self.weights.get(behavior, 0)
                score += weight
                reasons.append(f"Detected current behavior: {behavior} (+{weight})")
                active_behaviors.append(behavior)
                
        # 2. Historical Multiplier
        # If a person has previous suspicious activity, increase risk faster.
        history_penalty = 0
        if memory.loiter_count > 1:
            history_penalty += 10
            reasons.append(f"Recurrent loitering: Seen loitering {memory.loiter_count} times (+10)")
            
        if memory.zone_intrusions > 0:
            history_penalty += 15
            reasons.append(f"History of zone intrusions: {memory.zone_intrusions} previously (+15)")
            
        # Optional: Weighted history of past risk scores
        if memory.risk_history:
            avg_past_risk = sum(memory.risk_history) / len(memory.risk_history)
            if avg_past_risk > 40:
                history_penalty += 20
                reasons.append(f"High historical average risk score: {int(avg_past_risk)} (+20)")
                
        score += history_penalty
        
        return score, reasons, active_behaviors
