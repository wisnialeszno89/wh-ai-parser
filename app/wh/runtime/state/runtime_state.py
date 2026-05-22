from dataclasses import dataclass, field

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)

from app.wh.runtime.state.action_history import (
    ActionHistory
)


@dataclass
class RuntimeState:

    connected: bool = False

    active_tool: RuntimeTool | None = None

    history: ActionHistory = field(
        default_factory=ActionHistory
    )