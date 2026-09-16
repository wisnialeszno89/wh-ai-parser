from app.agent.agent_request import AgentRequest
from app.agent.session.agent_session_store import AgentSessionStore

from app.agent.agent_intent import AgentIntent

from app.agent.offers.offer_workflow_service import (
    OfferWorkflowService,
)

from app.agent.execution.default_executors import (
    create_default_executor_registry,
)

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.execution.plan_executor import (
    PlanExecutor,
)

from app.agent.runtime.agent_orchestrator import (
    AgentOrchestrator,
)

from app.agent.runtime.agent_runtime_result import (
    AgentRuntimeResult,
)


class AgentRuntime:
    """
    Main runtime entry point for the agent.

    The runtime connects:

    AgentRequest
        ->
    AgentOrchestrator
        ->
    AgentExecutionContext
        ->
    PlanExecutor
        ->
    ExecutionEngine
        ->
    ExecutorRegistry
        ->
    AgentRuntimeResult

    UI, API and automation systems should eventually
    communicate with the agent through this runtime.
    """

    def __init__(
        self,
        orchestrator: (
            AgentOrchestrator | None
        ) = None,
        plan_executor: (
            PlanExecutor | None
        ) = None,
        session_store: AgentSessionStore | None = None,
    ) -> None:

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else AgentOrchestrator()
        )

        self.session_store = (
            session_store
            if session_store is not None
            else AgentSessionStore()
        )

        if plan_executor is not None:
            self.plan_executor = plan_executor
        else:
            registry = (
                create_default_executor_registry()
            )

            engine = ExecutionEngine(
                registry=registry
            )

            self.plan_executor = PlanExecutor(
                engine=engine
            )

    def run(
        self,
        request: AgentRequest,
    ) -> AgentRuntimeResult:
        """
        Execute one complete agent cycle.
        """

        session = None
        offer_workflow_result = None

        if request.session_id is not None:
            session = self.session_store.get_or_create(
                session_id=request.session_id,
                salesman_id=request.salesman_id,
            )
            session.remember(request.message)

        if (
            session is not None
            and session.state.offer_session.current_context
            is not None
        ):
            request = AgentRequest(
                message=request.message,
                session_id=request.session_id,
                salesman_id=request.salesman_id,
                metadata={
                    **request.metadata,
                    "continuation_of_offer": True,
                },
            )

        context = (
            self.orchestrator.prepare(
                request
            )
        )

        if (
            context.intent == AgentIntent.CREATE_QUOTE
            and session is not None
        ):
            offer_workflow_result = (
                OfferWorkflowService().process(
                    session.state.offer_session,
                    request.message,
                )
            )

            session.state.offer_session = (
                offer_workflow_result.session
            )

            self.session_store.save(session)

            context.set_value(
                "offer_context",
                offer_workflow_result.current_context,
            )

            context.set_value(
                "offer_workflow_result",
                offer_workflow_result,
            )

            context.set_value(
                "offer_workflow_state",
                offer_workflow_result.workflow_state,
            )

        if (
            context.requires_manual_review
            or context.plan is None
        ):
            return AgentRuntimeResult(
                intent=context.intent,
                context=context,
                execution_report=None,
                requires_manual_review=True,
                executed=False,
            )

        execution_report = (
            self.plan_executor.execute(
                plan=context.plan,
                context=context,
            )
        )

        return AgentRuntimeResult(
            intent=context.intent,
            context=context,
            execution_report=execution_report,
            requires_manual_review=(
                context.requires_manual_review
                or execution_report.requires_manual_review
            ),
            executed=True,
        )
