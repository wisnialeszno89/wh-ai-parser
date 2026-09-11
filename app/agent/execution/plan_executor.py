from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.execution.plan_execution_report import (
    PlanExecutionReport,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class PlanExecutor:
    """
    Executes an ActionPlan step by step using a shared context.

    The context survives the complete execution lifecycle and can
    be enriched by individual executors.
    """

    def __init__(
        self,
        engine: ExecutionEngine,
    ) -> None:
        self.engine = engine

    def execute(
        self,
        plan: ActionPlan,
        context: ExecutionContext,
    ) -> PlanExecutionReport:

        results = []

        for step in plan.steps:

            result = self.engine.execute(
                step.action,
                context,
            )

            results.append(result)

            if not result.success:
                break

            if result.requires_manual_review:
                break

        return PlanExecutionReport(
            results=tuple(results)
        )
