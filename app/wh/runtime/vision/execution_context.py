from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


@dataclass
class ExecutionContext:

    mode: AdaptiveExecutionMode

    retry_count: int = 3

    enable_logging: bool = False

    enable_recovery: bool = False

    enable_screenshots: bool = False