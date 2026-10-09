from __future__ import annotations

import os

from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
)
from app.agent.reasoning.openai_task_reasoner import (
    OpenAITaskReasoner,
)
from app.agent.reasoning.openai_plan_reasoner import (
    OpenAIPlanReasoner,
)
from app.agent.reasoning.plan_reasoner import PlanReasoner
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def _configured_task_reasoner() -> TaskReasoner:
    """Select exactly one configured task-reasoning provider.

    NaviMind is preferred whenever its endpoint is present. A missing
    NaviMind credential is a configuration error, never a reason to silently
    switch to another remote provider.
    """
    navimind_url = os.getenv("NAVIMIND_AGENT_URL", "").strip()

    if navimind_url:
        return NaviMindTaskReasoner()

    if os.getenv("AGENT_TASK_REASONING", "").strip() == "1":
        return OpenAITaskReasoner()

    raise RuntimeError(
        "No task reasoner is configured. Set NAVIMIND_AGENT_URL and "
        "NAVIMIND_AGENT_SECRET, or explicitly set AGENT_TASK_REASONING=1 "
        "and configure OPENAI_API_KEY."
    )


def create_windows_desktop_agent_runtime(
    *,
    task_reasoner: TaskReasoner | None = None,
    plan_reasoner: PlanReasoner | None = None,
) -> AgentRuntime:
    """Create the generic Windows desktop runtime with required task reasoning.

    The selected task reasoner proposes semantic actions only. The existing
    local orchestrator, target validation, Windows control loop, executor,
    safety gate and verification path remain responsible for execution.

    Physical GUI execution remains DRY_RUN unless COMPUTER_REAL=1 is explicitly
    present in the local process environment.
    """
    selected_task_reasoner = (
        task_reasoner
        if task_reasoner is not None
        else _configured_task_reasoner()
    )

    selected_plan_reasoner = plan_reasoner
    if (
        selected_plan_reasoner is None
        and os.getenv("AGENT_PLAN_REASONING", "").strip() == "1"
    ):
        selected_plan_reasoner = OpenAIPlanReasoner()

    return AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=selected_task_reasoner,
            require_task_reasoning=True,
        ),
        control_loop=create_windows_desktop_agent_control_loop(
            plan_reasoner=selected_plan_reasoner,
        ),
    )
