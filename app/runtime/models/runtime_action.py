from dataclasses import dataclass
from typing import Any


@dataclass
class RuntimeAction:

    action: str

    payload: Any = None