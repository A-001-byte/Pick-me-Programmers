from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PersonMemory:
    """Represents the active historical memory for a tracked person."""
    person_id: int
    loiter_count: int = 0
    zone_intrusions: int = 0
    weapon_events: int = 0
    risk_history: List[int] = field(default_factory=list)
    last_seen: Optional[float] = None
