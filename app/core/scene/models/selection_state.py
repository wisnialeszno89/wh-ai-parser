from dataclasses import dataclass
from typing import Optional


@dataclass
class SelectionState:

    selected_object_id: Optional[str] = None

    selected_tool: Optional[str] = None

    edit_mode: bool = False