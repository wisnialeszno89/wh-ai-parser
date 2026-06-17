from dataclasses import dataclass
from typing import Optional


@dataclass
class RuntimeCommand:

    command_type: str

    x: Optional[int] = None
    y: Optional[int] = None

    text: Optional[str] = None