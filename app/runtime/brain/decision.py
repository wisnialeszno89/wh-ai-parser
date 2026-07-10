from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Decision:

    action: Any

    reason: str