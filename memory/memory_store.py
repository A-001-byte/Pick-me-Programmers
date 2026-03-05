from typing import Dict, List
from memory.person_memory import PersonMemory
from utils.time_utils import get_current_time_seconds
from utils.config_loader import load_json_config
import os

class MemoryStore:
    """Manages tracking of person behavior history and state decay."""
    
    def __init__(self):
        self.active_persons: Dict[int, PersonMemory] = {}
        
        # Load expiry config
        # Using a default path, but robustly handling if missing
        decay_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "decay_config.json")
        config = load_json_config(decay_config_path)
        
        # Minutes to seconds
        self.expiry_seconds = config.get("memory_expiry_minutes", 10) * 60

    def clean_expired(self):
        """Removes records that haven't been seen recently."""
        current_time = get_current_time_seconds()
        expired_keys = []
        for pid, memory in self.active_persons.items():
            if memory.last_seen and (current_time - memory.last_seen > self.expiry_seconds):
                expired_keys.append(pid)
                
        for pid in expired_keys:
            del self.active_persons[pid]

    def get_person(self, person_id: int) -> PersonMemory:
        """Retrieves or creates memory for a person."""
        self.clean_expired()
        if person_id not in self.active_persons:
            self.active_persons[person_id] = PersonMemory(person_id=person_id, last_seen=get_current_time_seconds())
        return self.active_persons[person_id]
        
    def update_person(self, person_id: int, behaviors: List[str], current_score: int):
        """Updates counts and timestamps based on current behavior observations."""
        person_memory = self.get_person(person_id)
        
        if "loitering" in behaviors:
            person_memory.loiter_count += 1
        if "zone_intrusion" in behaviors:
            person_memory.zone_intrusions += 1
        if "weapon_detected" in behaviors:
            person_memory.weapon_events += 1
            
        person_memory.risk_history.append(current_score)
        
        # Maintain a rolling window of history (e.g., last 10 scores) to save memory
        if len(person_memory.risk_history) > 10:
            person_memory.risk_history = person_memory.risk_history[-10:]
            
        person_memory.last_seen = get_current_time_seconds()
        self.active_persons[person_id] = person_memory
