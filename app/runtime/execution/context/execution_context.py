from app.runtime.execution.screen_cache import (
    ScreenCache,
)


class ExecutionContext:

    def __init__(

        self,

        mouse_enabled=False,

    ):

        self.mouse_enabled = mouse_enabled

        self.cache = ScreenCache()