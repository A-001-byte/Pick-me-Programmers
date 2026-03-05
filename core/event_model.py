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
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(**data)
