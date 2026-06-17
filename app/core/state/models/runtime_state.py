from dataclasses import dataclass
from typing import Optional


@dataclass
class RuntimeState:

    workflow_step: str

    active_tool: Optional[str] = None

    last_action: Optional[str] = None

    is_waiting_for_input: bool = False