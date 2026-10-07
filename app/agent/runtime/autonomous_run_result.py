from dataclasses import dataclass

from app.agent.runtime.agent_runtime_result import AgentRuntimeResult
from app.agent.runtime.reasoning_usage import ReasoningCostSummary


@dataclass(frozen=True)
class AutonomousRunResult:
    """Result of one goal-driven autonomous execution session."""

    session_id: str
    step_results: tuple[AgentRuntimeResult, ...]
    success: bool
    completed: bool
    requires_manual_review: bool
    stopped: bool
    reason: str
    reasoning_calls: int = 0
    reasoning_cost: ReasoningCostSummary = ReasoningCostSummary()

    @property
    def executed_actions(self) -> int:
        return sum(
            result.control_loop_result.executed_actions
            for result in self.step_results
            if result.control_loop_result is not None
        )
