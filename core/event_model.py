from dataclasses import dataclass, asdict, fields
from typing import Dict, Any, List, Union


@dataclass
class Event:
    person_id: str
    bbox: List[Union[int, float]]
    event_type: str
    risk_score: float
    timestamp: Union[float, str]
    camera_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        from dataclasses import MISSING
        required_fields = [
            f.name for f in fields(cls) 
            if f.default is MISSING and f.default_factory is MISSING
        ]
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        valid_names = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_names}
        return cls(**filtered)
