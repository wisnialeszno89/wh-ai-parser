from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.windowhub_agent_control_loop import (
    create_windowhub_agent_control_loop,
)


def create_windowhub_agent_runtime() -> AgentRuntime:
    """
    Create the Universal Agent Runtime connected to WindowHub.

    The runtime keeps request orchestration and execution under
    the same universal AgentRuntime entry point while WindowHub
    remains an environment adapter.
    """

    return AgentRuntime(
        control_loop=create_windowhub_agent_control_loop(),
    )
