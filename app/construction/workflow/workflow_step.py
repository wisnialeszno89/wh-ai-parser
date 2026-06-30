from dataclasses import dataclass
from typing import Any


@dataclass
class WorkflowStep:

    operation: str

    payload: Any = None