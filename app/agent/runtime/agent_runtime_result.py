from dataclasses import dataclass

from app.agent.agent_intent import AgentIntent
from app.agent.execution.plan_execution_report import (
    PlanExecutionReport,
)
from app.agent.runtime.execution_context import (
    AgentExecutionContext,
)
from app.agent.runtime.control_loop_result import (
    ControlLoopResult,
)
from app.agent.runtime.confirmation import (
    ConfirmationRequest,
)


@dataclass(frozen=True)
class AgentRuntimeResult:
    """
    Final result returned by the complete agent runtime.

    This represents one complete agent cycle:

    request
        ->
    orchestration
        ->
    planning
        ->
    capability selection
        ->
    skill selection
        ->
    execution
    """

    intent: AgentIntent

    context: AgentExecutionContext

    execution_report: (
        PlanExecutionReport | None
    )

    requires_manual_review: bool

    executed: bool

    control_loop_result: ControlLoopResult | None = None

    # Present when execution was stopped at a confirmation boundary.
    confirmation_request: ConfirmationRequest | None = None
