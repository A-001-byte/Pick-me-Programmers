from config.risk_weights import BEHAVIOR_WEIGHTS
from risk_engine.memory_store import MemoryStore
from risk_engine.risk_levels import get_risk_level
from utils.logger import get_logger

logger = get_logger("RiskCalculator")

class RiskCalculator:
    """
    Computes a risk score and risk level for a person based on current signals
    and short-term behavioral memory.
    """
    def __init__(self):
        # Initialize memory for tracking recent behaviors
        self.memory_store = MemoryStore()

    def process_event(self, event):
        """
        Process an incoming signal event and returns the calculated risk output.
        
        Combines current behavior scores with penalties if the person 
        was already exhibiting suspicious behavior recently.
        """
        person_id = event.get("person_id")
        current_behaviors = event.get("behaviors", [])
        
        logger.info(f"Computing risk for Person ID {person_id}. Behaviors detected: {current_behaviors}")
        
        # 1. Look up any past behaviors in short-term memory
        previous_behaviors = self.memory_store.get_person_behaviors(person_id)
        
        # 2. Calculate the base score out of current behaviors
        total_score = 0
        for behavior in current_behaviors:
            total_score += BEHAVIOR_WEIGHTS.get(behavior, 0)
            
        # 3. Memory Feature: Increase risk faster if there's a history of bad behavior
        # Example: if they have a history record for previous actions, add an extra penalty 
        # based on past behaviors to increase the new overall risk score.
        if previous_behaviors:
            memory_penalty = sum(BEHAVIOR_WEIGHTS.get(b, 0) for b in previous_behaviors)
            # Add 50% of their historical weight onto current action penalty as escalation
            total_score += int(memory_penalty * 0.5) 
        
        # 4. Determine risk level grouping
        risk_level = get_risk_level(total_score)
        
        # 5. Output decision 
        result = {
            "person_id": person_id,
            "risk_score": total_score,
            "risk_level": risk_level,
            "previous_behaviors": previous_behaviors  # The behaviors before this current event
        }
        
        # 6. Finally, update the person's memory record including these new behaviors
        self.memory_store.update_person_memory(person_id, current_behaviors)
        
        return result
