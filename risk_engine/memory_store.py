import time
from config.risk_weights import MEMORY_EXPIRY_SECONDS

class MemoryStore:
    """
    Maintains a dictionary-based short-term memory of recent behaviors per person.
    Automatically expires old entries based on the configured time limit.
    """
    def __init__(self):
        # Format: { person_id: { "behaviors": ["loitering"], "last_updated": 1678000000.0 } }
        self.memory = {}

    def clean_expired(self):
        """Removes expired entries from memory."""
        current_time = time.time()
        expired_keys = []
        
        for pid, data in self.memory.items():
            if current_time - data["last_updated"] > MEMORY_EXPIRY_SECONDS:
                expired_keys.append(pid)
                
        for pid in expired_keys:
            del self.memory[pid]

    def get_person_behaviors(self, person_id):
        """Retrieves prior active behaviors for a person if they haven't expired."""
        self.clean_expired()
        if person_id in self.memory:
            return self.memory[person_id]["behaviors"]
        return []

    def update_person_memory(self, person_id, current_behaviors):
        """Updates the memory for a person with new behaviors."""
        self.clean_expired()
        
        # Initialize dictionary entry if person isn't tracked yet
        if person_id not in self.memory:
            self.memory[person_id] = {"behaviors": [], "last_updated": time.time()}
            
        # Add new behaviors (avoiding duplicates)
        for b in current_behaviors:
            if b not in self.memory[person_id]["behaviors"]:
                self.memory[person_id]["behaviors"].append(b)
                
        # Update the timestamp
        self.memory[person_id]["last_updated"] = time.time()
