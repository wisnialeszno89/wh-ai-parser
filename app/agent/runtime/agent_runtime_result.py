from dataclasses import dataclass

from app.agent.agent_intent import AgentIntent
from app.agent.execution.plan_execution_report import (
    PlanExecutionReport,
)
from app.agent.runtime.execution_context import (
    AgentExecutionContext,
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
