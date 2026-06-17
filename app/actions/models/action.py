from dataclasses import dataclass
from typing import Optional


@dataclass
class Action:

    action_type: str

    target_id: Optional[str] = None

    tool_name: Optional[str] = None

    value: Optional[str] = None