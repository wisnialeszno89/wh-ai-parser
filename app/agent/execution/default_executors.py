from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
)
from app.agent.execution.action_executor import (
    ActionExecutor,
)
from app.agent.execution.browser_action_executor import (
    BrowserActionExecutor,
)
from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)
from app.agent.execution.wh_action_executor import (
    WHActionExecutor,
)


def create_default_executor_registry(
    *,
    browser_adapter: BrowserAdapter | None = None,
    additional_executors: tuple[ActionExecutor, ...] = (),
) -> ExecutorRegistry:
    """
    Create the default controlled executor registry.

    Browser execution is opt-in through an explicitly injected
    BrowserAdapter. This keeps the default runtime fail-closed when no
    browser provider is configured.
    """

    browser_executors: tuple[ActionExecutor, ...] = ()

    if browser_adapter is not None:
        browser_executors = (
            BrowserActionExecutor(browser_adapter),
        )

    return ExecutorRegistry(
        executors=(
            WHActionExecutor(),
            *browser_executors,
            *additional_executors,
        )
    )
