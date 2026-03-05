from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PersonMemory:
    """Represents the active historical memory for a tracked person."""
    person_id: int
    loiter_count: int = 0           # Count of loitering EVENTS (not frames)
    zone_intrusions: int = 0
    weapon_events: int = 0
    risk_history: List[int] = field(default_factory=list)
    last_seen: Optional[float] = None
    
    # State tracking for event-based counting (not per-frame)
    _was_loitering: bool = False
    _was_in_zone: bool = False
    _had_weapon: bool = False
