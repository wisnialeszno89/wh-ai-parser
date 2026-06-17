from app.runtime.agent_memory import (
    AgentMemory
)

from app.runtime.agent_metrics import (
    AgentMetrics
)

from app.runtime.retry_policy import (
    RetryPolicy
)

from app.runtime.agent_state import (
    AgentState
)


class AgentContext:

    def __init__(

        self

    ):

        self.memory = AgentMemory()

        self.metrics = AgentMetrics()

        self.retry_policy = RetryPolicy()

        self.state = AgentState.IDLE