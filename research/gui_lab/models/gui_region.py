from dataclasses import dataclass, field
import numpy as np


@dataclass(slots=True)
class GUIRegion:

    id: int

    x: int
    y: int

    width: int
    height: int

    roi: np.ndarray

    fingerprint = None

    semantic_role = None

    controls: list = field(
        default_factory=list
    )