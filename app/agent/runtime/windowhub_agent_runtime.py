import os

from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.reasoning.openai_task_reasoner import (
    OpenAITaskReasoner,
)
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

    task_reasoner = None

    if os.environ.get("AGENT_TASK_REASONING") == "1":
        task_reasoner = OpenAITaskReasoner()

    return AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=task_reasoner,
        ),
        control_loop=create_windowhub_agent_control_loop(),
    )
