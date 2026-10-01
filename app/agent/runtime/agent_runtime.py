from uuid import uuid4

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

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.agent_runtime_result import (
    AgentRuntimeResult,
)


class AgentRuntime:
    """
    Main runtime entry point for the agent.
    """

    @staticmethod
    def _offer_workflow_planning_context(
        result,
    ) -> dict[str, object]:
        context = result.current_context
        validation = result.validation

        offer_context = None

        if context is not None:
            offer_context = {
                "width": context.width,
                "height": context.height,
                "quantity": context.quantity,
                "product_type": context.product_type,
                "profile": context.profile,
                "configuration": context.configuration,
                "opening": context.opening,
                "openings": context.openings,
                "color_inside": context.color_inside,
                "color_outside": context.color_outside,
                "glazing": context.glazing,
            }

        return {
            "workflow_state": result.workflow_state.value,
            "is_ready_for_pricing": result.is_ready_for_pricing,
            "requires_salesperson_input": (
                result.requires_salesperson_input
            ),
            "questions": tuple(result.questions),
            "missing_fields": tuple(validation.missing_fields),
            "conflicts": tuple(validation.conflicts),
            "offer_context": offer_context,
        }

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        plan_executor: PlanExecutor | None = None,
        session_store: AgentSessionStore | None = None,
        control_loop: AgentControlLoop | None = None,
    ) -> None:

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else AgentOrchestrator()
        )

        self.control_loop = control_loop

        self.session_store = (
            session_store
            if session_store is not None
            else AgentSessionStore()
        )

        if plan_executor is not None:
            self.plan_executor = plan_executor
        else:
            registry = create_default_executor_registry()

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
        planning_offer_workflow = None

        # ---------------------------------------------------------
        # Existing session: restore offer continuation BEFORE
        # orchestration so modifiers such as "DKR, 2 sztuki"
        # remain part of the active quote workflow.
        # ---------------------------------------------------------

        if request.session_id is not None:
            session = self.session_store.get_or_create(
                session_id=request.session_id,
                salesman_id=request.salesman_id,
            )

            session.remember(request.message)

            if (
                session.state.offer_session.current_context
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

        # ---------------------------------------------------------
        # Initial intent resolution.
        #
        # Use the orchestrator's public API so lightweight test
        # doubles and custom orchestrators remain compatible.
        # ---------------------------------------------------------

        context = self.orchestrator.prepare(
            request,
            initial_scene=None,
            offer_workflow=None,
        )

        detected_intent = context.intent

        # ---------------------------------------------------------
        # Build semantic offer workflow context BEFORE the final
        # planning pass for CREATE_QUOTE requests.
        #
        # The first prepare() above is intentionally side-effect free;
        # it lets custom orchestrators participate without requiring
        # access to an internal planner attribute.
        # ---------------------------------------------------------

        if detected_intent == AgentIntent.CREATE_QUOTE:
            if session is None:
                session_id = (
                    request.session_id
                    or f"runtime-offer-{uuid4().hex}"
                )

                session = self.session_store.get_or_create(
                    session_id=session_id,
                    salesman_id=request.salesman_id,
                )

                session.remember(request.message)

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

            planning_offer_workflow = (
                self._offer_workflow_planning_context(
                    offer_workflow_result
                )
            )

        # ---------------------------------------------------------
        # Initial world-state observation.
        #
        # The planner must see the current semantic UI state before
        # the final action plan is created.
        # ---------------------------------------------------------

        initial_scene = None

        if self.control_loop is not None:
            try:
                initial_scene = (
                    self.control_loop.observe_scene()
                )
            except Exception as exc:
                context = self.orchestrator.prepare(
                    request,
                    initial_scene=None,
                    offer_workflow=planning_offer_workflow,
                )

                context.set_value(
                    "initial_observation_error",
                    str(exc),
                )

                context.requires_manual_review = True

                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

        # ---------------------------------------------------------
        # Final orchestration pass with observed world state and
        # structured offer workflow context.
        #
        # For legacy/custom orchestrators that do not accept the new
        # keyword arguments, retain the older prepare(request) contract.
        # ---------------------------------------------------------

        try:
            context = self.orchestrator.prepare(
                request,
                initial_scene=initial_scene,
                offer_workflow=planning_offer_workflow,
            )
        except TypeError as exc:
            if (
                "initial_scene" not in str(exc)
                and "offer_workflow" not in str(exc)
            ):
                raise

            try:
                context = self.orchestrator.prepare(
                    request,
                    initial_scene=initial_scene,
                )
            except TypeError as exc:
                if "initial_scene" not in str(exc):
                    raise

                context = self.orchestrator.prepare(
                    request
                )

        if initial_scene is not None:
            context.update_scene(initial_scene)

        # ---------------------------------------------------------
        # Persist semantic offer workflow state into the execution
        # context after orchestration.
        # ---------------------------------------------------------

        if offer_workflow_result is not None:
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

            context.set_value(
                "offer_workflow_planning",
                planning_offer_workflow,
            )

        # ---------------------------------------------------------
        # Workflow safety gate.
        #
        # The universal control-loop path must never turn an
        # incomplete structured offer into GUI execution. The legacy
        # executor remains responsible for its existing validation /
        # manual-review behavior so its established contract stays
        # intact.
        # ---------------------------------------------------------

        if (
            self.control_loop is not None
            and offer_workflow_result is not None
            and offer_workflow_result.requires_salesperson_input
        ):
            context.requires_manual_review = True
            context.set_value(
                "salesperson_questions",
                offer_workflow_result.questions,
            )

            return AgentRuntimeResult(
                intent=context.intent,
                context=context,
                execution_report=None,
                requires_manual_review=True,
                executed=False,
            )

        # ---------------------------------------------------------
        # Manual review / missing plan.
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Execute semantic plan through the universal control loop
        # when an environment runtime is configured.
        # ---------------------------------------------------------

        if self.control_loop is not None:
            control_loop_result = self.control_loop.run(
                plan=context.plan,
                context=context,
            )

            return AgentRuntimeResult(
                intent=context.intent,
                context=context,
                execution_report=None,
                control_loop_result=control_loop_result,
                requires_manual_review=(
                    context.requires_manual_review
                    or control_loop_result.requires_manual_review
                ),
                executed=True,
            )

        # ---------------------------------------------------------
        # Backward-compatible semantic execution path used when
        # no environment-specific control loop is configured.
        # ---------------------------------------------------------

        execution_report = self.plan_executor.execute(
            plan=context.plan,
            context=context,
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
