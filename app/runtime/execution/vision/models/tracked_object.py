from dataclasses import dataclass
from enum import Enum

from app.runtime.execution.vision.models.logical_object import LogicalObject


class TrackedObjectStatus(str, Enum):
    NEW = "new"
    STABLE = "stable"
    MOVED = "moved"
    LOST = "lost"


@dataclass(slots=True)
class TrackedObject:
    id: str
    object: LogicalObject
    control_type: str | None = None
    confidence: float = 0.0
    first_seen: int = 0
    last_seen: int = 0
    observation_count: int = 0
    consecutive_observations: int = 0
    consecutive_missed_frames: int = 0
    status: TrackedObjectStatus = TrackedObjectStatus.NEW
    stability: float = 0.0
