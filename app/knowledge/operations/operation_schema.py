from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Operation:

    operation: str

    params: Dict[str, Any]