import os
from collections.abc import Callable

from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.knowledge.windowhub_offer_knowledge import (
    get_windowhub_offer_knowledge,
)
from app.agent.offers.offer_request_parameter_resolver import (
    OfferRequestParameterResolver,
)


def create_windowhub_agent_runtime(
    *,
    control_loop_factory: Callable[..., object] | None = None,
) -> AgentRuntime:
    """
    Create the Universal Agent Runtime connected to WindowHub.

    The runtime keeps request orchestration and execution under
    the same universal AgentRuntime entry point while WindowHub
    remains an environment adapter.
    """

    task_reasoner = None
    plan_reasoner = None

    # Provider imports stay lazy so read-only diagnostics and dependency-injected
    # tests do not require a configured remote reasoning provider.
    if os.environ.get("NAVIMIND_AGENT_URL", "").strip():
        from app.agent.reasoning.navimind_task_reasoner import (
            NaviMindTaskReasoner,
        )
        from app.agent.reasoning.openai_plan_reasoner import OpenAIPlanReasoner

        task_reasoner = NaviMindTaskReasoner()
        plan_reasoner = OpenAIPlanReasoner()
    elif os.environ.get("AGENT_TASK_REASONING") == "1":
        from app.agent.reasoning.openai_task_reasoner import OpenAITaskReasoner
        from app.agent.reasoning.openai_plan_reasoner import OpenAIPlanReasoner

        task_reasoner = OpenAITaskReasoner()
        plan_reasoner = OpenAIPlanReasoner()

    if control_loop_factory is None:
        from app.agent.runtime.windowhub_agent_control_loop import (
            create_windowhub_agent_control_loop,
        )

        control_loop_factory = create_windowhub_agent_control_loop

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=task_reasoner,
            application_knowledge=(
                get_windowhub_offer_knowledge()
            ),
            require_task_reasoning=True,
        ),
        control_loop=control_loop_factory(
            plan_reasoner=plan_reasoner,
        ),
        learned_parameter_resolver=(
            OfferRequestParameterResolver().resolve
        ),
    )
    # This only wires the existing environment dependencies to the persisted
    # task service. No observation or GUI action occurs until explicitly advanced.
    runtime.configure_windowhub_resumable_tasks()
    return runtime
