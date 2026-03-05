# Configuration for Risk Weights and System Parameters

# Weights assigned to specific behaviors detected by other modules
BEHAVIOR_WEIGHTS = {
    "loitering": 20,
    "zone_intrusion": 30,
    "running_fast": 15,
    "weapon_detected": 80
}

# Time to live (TTL) for short-term memory in seconds
# e.g., 300 seconds = 5 minutes of memory history before it expires
MEMORY_EXPIRY_SECONDS = 300 
