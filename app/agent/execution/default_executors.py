from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)
from app.agent.execution.wh_action_executor import (
    WHActionExecutor,
)


def create_default_executor_registry(
) -> ExecutorRegistry:
    """
    Create the default controlled executor registry.

    New executors can later be added here for:

    - Excel
    - Word
    - Browser
    - CAD
    - API
    """

    return ExecutorRegistry(
        executors=(
            WHActionExecutor(),
        )
    )
