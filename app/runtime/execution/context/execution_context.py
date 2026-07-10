from app.runtime.execution.execution_mode import (
    ExecutionMode,
)

from app.runtime.execution.screen_cache import (
    ScreenCache,
)


class ExecutionContext:

    def __init__(

        self,

        mouse_enabled=False,

        execution_mode=ExecutionMode.LIVE,

    ):

        self.mouse_enabled = mouse_enabled

        self.execution_mode = execution_mode

        self.cache = ScreenCache()