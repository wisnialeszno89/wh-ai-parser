from dataclasses import dataclass

from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object import LogicalObject


@dataclass(frozen=True, slots=True)
class VisionObjectObservation:
    logical_object: LogicalObject
    control_type: ControlType
    confidence: float
