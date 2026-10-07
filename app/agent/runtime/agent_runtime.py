from uuid import uuid4

from app.agent.agent_request import AgentRequest
from app.agent.adapters.browser_adapter import BrowserAdapter, BrowserPage
from app.agent.session.agent_session_store import AgentSessionStore

from app.agent.agent_intent import AgentIntent
from app.agent.learning.agent_mode import AgentMode
from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayer,
)
from app.agent.learning.learned_workflow_service import (
    LearnedWorkflowService,
)
from app.agent.memory.agent_memory import AgentExperience

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
from app.agent.runtime.execution_context import (
    AgentExecutionContext,
)
from app.agent.runtime.autonomous_run_result import (
    AutonomousRunResult,
)
from app.agent.runtime.browser_action_risk_policy import (
    BrowserActionRiskPolicy,
)
from app.agent.runtime.confirmation import (
    ConfirmationRequest,
    action_confirmation_key,
)
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.reasoning.knowledge_context import KnowledgeContext


class AgentRuntime:
    """
    Main runtime entry point for the agent.
    """

    @staticmethod
    def _offer_workflow_planning_context(
        result,
        *,
        continuation_of_offer: bool = False,
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
            "continuation_of_offer": continuation_of_offer,
        }

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        plan_executor: PlanExecutor | None = None,
        session_store: AgentSessionStore | None = None,
        control_loop: AgentControlLoop | None = None,
        learned_parameter_resolver=None,
        browser_adapter: BrowserAdapter | None = None,
        browser_context_enabled: bool = False,
    ) -> None:

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else AgentOrchestrator()
        )

        self.control_loop = control_loop
        self.learned_parameter_resolver = learned_parameter_resolver
        self.browser_adapter = browser_adapter
        self.browser_context_enabled = browser_context_enabled

        # One-time confirmation grants live only in this runtime process.
        # The token is opaque and is bound to an exact semantic action and
        # session, so an approval cannot be replayed for another action.
        self._pending_confirmations: dict[
            str,
            tuple[str, str, str],
        ] = {}

        self.session_store = (
            session_store
            if session_store is not None
            else AgentSessionStore()
        )

        if plan_executor is not None:
            self.plan_executor = plan_executor
        else:
            registry = create_default_executor_registry(
                browser_adapter=browser_adapter,
            )

            engine = ExecutionEngine(
                registry=registry
            )

            self.plan_executor = PlanExecutor(
                engine=engine
            )

    @staticmethod
    def _is_gui_reasoning_plan(plan) -> bool:
        if plan is None or not plan.steps:
            return False

        return all(
            step.action.name
            in {
                "click_screen_element",
                "write_text",
            }
            for step in plan.steps
        )

    def _try_execute_learned_workflow(
        self,
        request: AgentRequest,
        *,
        initial_scene=None,
    ) -> AgentRuntimeResult | None:
        """Resolve an exact learned skill before generic task planning.

        Learned replay is an explicit high-confidence skill path. Once an
        exact trigger is resolved, its success or failure is returned to the
        caller instead of silently falling back to a different plan.
        """
        if self.control_loop is None:
            return None

        if request.mode != AgentMode.EXECUTE:
            return None

        if request.metadata.get(
            "disable_learned_workflow_replay"
        ) is True:
            return None

        workflow_memory_store = getattr(
            self.orchestrator,
            "workflow_memory_store",
            None,
        )
        if workflow_memory_store is None:
            return None

        application = None
        if initial_scene is not None:
            application = (
                initial_scene.observation.state.active_application
            )

        execution = LearnedWorkflowService(
            memory_store=workflow_memory_store,
            control_loop=self.control_loop,
            min_score=0.99,
            parameter_resolver=self.learned_parameter_resolver,
        ).execute(
            request,
            application=application,
        )

        if execution is None:
            return None

        workflow = execution.match.workflow
        replay = execution.replay

        plan = LearnedWorkflowReplayer(
            control_loop=self.control_loop,
        ).build_plan(
            workflow,
            parameters=execution.parameters,
        )

        context = AgentExecutionContext(
            request=request,
            intent=AgentIntent.OBSERVE_WORKFLOW,
            plan=plan,
            capability=None,
            skill=None,
            requires_manual_review=not replay.success,
        )

        if initial_scene is not None:
            context.update_scene(initial_scene)

        context.set_value(
            "learned_workflow_id",
            workflow.workflow_id,
        )
        context.set_value(
            "learned_workflow_name",
            workflow.name,
        )
        context.set_value(
            "learned_workflow_match_score",
            execution.match.score,
        )
        context.set_value(
            "learned_workflow_match_reasons",
            execution.match.reasons,
        )
        context.set_value(
            "learned_workflow_parameters",
            dict(execution.parameters),
        )
        context.set_value(
            "learned_workflow_result",
            replay,
        )

        self._remember_experience(
            kind="learned_workflow_replay",
            application=application,
            intent=AgentIntent.OBSERVE_WORKFLOW.value,
            workflow_id=workflow.workflow_id,
            outcome="success" if replay.success else "failure",
            summary=(
                f"Replayed learned workflow '{workflow.name}'."
            ),
            metadata={
                "parameter_names": tuple(
                    sorted(
                        str(key)
                        for key in execution.parameters
                    )
                ),
                "completed_steps": replay.completed_steps,
                "total_steps": replay.total_steps,
            },
        )

        return AgentRuntimeResult(
            intent=AgentIntent.OBSERVE_WORKFLOW,
            context=context,
            execution_report=None,
            requires_manual_review=not replay.success,
            executed=True,
            control_loop_result=replay.control_loop_result,
        )

    def _prepare_context(
        self,
        request: AgentRequest,
        *,
        initial_scene=None,
        offer_workflow=None,
        autonomous: bool = False,
        browser_page: BrowserPage | None = None,
    ):
        external_knowledge = None
        raw_external_knowledge = request.metadata.get(
            "external_knowledge"
        )

        if raw_external_knowledge is not None:
            try:
                external_knowledge = KnowledgeContext.from_payload(
                    raw_external_knowledge
                )
            except (TypeError, ValueError):
                external_knowledge = None

        try:
            try:
                return self.orchestrator.prepare(
                    request,
                    initial_scene=initial_scene,
                    browser_page=browser_page,
                    offer_workflow=offer_workflow,
                    external_knowledge=external_knowledge,
                    autonomous=autonomous,
                )
            except TypeError as exc:
                if "autonomous" not in str(exc):
                    raise
                return self.orchestrator.prepare(
                    request,
                    initial_scene=initial_scene,
                    browser_page=browser_page,
                    offer_workflow=offer_workflow,
                    external_knowledge=external_knowledge,
                )
        except TypeError as exc:
            if "offer_workflow" in str(exc):
                try:
                    return self.orchestrator.prepare(
                        request,
                        initial_scene=initial_scene,
                        external_knowledge=external_knowledge,
                        autonomous=autonomous,
                    )
                except TypeError as nested_exc:
                    if "initial_scene" not in str(nested_exc):
                        raise
                    return self.orchestrator.prepare(
                        request,
                        external_knowledge=external_knowledge,
                        autonomous=autonomous,
                    )
            if "initial_scene" in str(exc):
                return self.orchestrator.prepare(
                    request,
                    external_knowledge=external_knowledge,
                    autonomous=autonomous,
                )
            raise

    def _consume_confirmation_token(
        self,
        request: AgentRequest,
        context,
    ) -> bool:
        token = request.metadata.get(
            "confirmation_token"
        )

        if token is None:
            return False

        if not isinstance(token, str) or not token.strip():
            context.requires_manual_review = True
            context.set_value(
                "task_reasoning_failure",
                "invalid_confirmation_token",
            )
            return False

        pending = self._pending_confirmations.get(
            token.strip()
        )

        if pending is None:
            context.requires_manual_review = True
            context.set_value(
                "task_reasoning_failure",
                "invalid_or_expired_confirmation_token",
            )
            return False

        session_id, original_goal, action_key = pending

        if request.session_id != session_id:
            context.requires_manual_review = True
            context.set_value(
                "task_reasoning_failure",
                "confirmation_token_session_mismatch",
            )
            return False

        plan = context.plan
        matching_action = None

        if plan is not None:
            for step in plan.steps:
                if (
                    action_confirmation_key(step.action)
                    == action_key
                ):
                    matching_action = step.action
                    break

        if matching_action is None:
            context.requires_manual_review = True
            context.set_value(
                "task_reasoning_failure",
                "confirmation_token_action_mismatch",
            )
            return False

        self._pending_confirmations.pop(
            token.strip(),
            None,
        )

        context.set_value(
            "confirmed_action_key",
            action_key,
        )
        return True

    def _create_confirmation_request(
        self,
        request: AgentRequest,
        context,
        control_loop_result,
    ) -> ConfirmationRequest | None:
        decisions = getattr(
            control_loop_result,
            "decisions",
            (),
        )

        if not decisions:
            return None

        decision = decisions[-1]
        metadata = getattr(
            decision,
            "metadata",
            {},
        )

        if (
            not isinstance(metadata, dict)
            or metadata.get("reason_code")
            != "confirmation_required"
        ):
            return None

        plan = context.plan
        if plan is None or not plan.steps:
            return None

        session_id = request.session_id
        if not isinstance(session_id, str) or not session_id.strip():
            return None

        action = next(
            (
                step.action
                for step in plan.steps
                if (
                    step.action.requires_confirmation
                    or BrowserActionRiskPolicy.requires_confirmation(
                        step.action
                    )
                )
            ),
            None,
        )
        if action is None:
            return None

        token = uuid4().hex
        confirmation = ConfirmationRequest(
            token=token,
            session_id=session_id,
            action_name=action.name,
            description=action.description,
            target=action.target,
            value=action.value,
        )

        self._pending_confirmations[token] = (
            session_id,
            request.message,
            action_confirmation_key(action),
        )

        context.set_value(
            "confirmation_request",
            confirmation.to_payload(),
        )

        return confirmation

    def run(
        self,
        request: AgentRequest,
        *,
        autonomous: bool = False,
    ) -> AgentRuntimeResult:
        """
        Execute one complete agent cycle.
        """

        session = None
        offer_workflow_result = None
        planning_offer_workflow = None

        # A confirmation token resumes the exact task that produced it.
        # Do not let a follow-up message silently replace that task goal
        # before the reasoning pass that validates the confirmed action.
        confirmation_token = request.metadata.get(
            "confirmation_token"
        )
        if isinstance(confirmation_token, str):
            pending = self._pending_confirmations.get(
                confirmation_token.strip()
            )
            if (
                pending is not None
                and request.session_id == pending[0]
            ):
                request = AgentRequest(
                    message=pending[1],
                    session_id=request.session_id,
                    salesman_id=request.salesman_id,
                    metadata=dict(request.metadata),
                    mode=request.mode,
                )

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

        # Observe first, then compute workflow context and finally
        # prepare the action plan exactly once.
        initial_scene = None
        browser_page = None

        browser_requested = (
            self.browser_context_enabled
            or (
                request.metadata.get("target_application")
                and str(
                    request.metadata.get(
                        "target_application"
                    )
                ).strip().casefold()
                == "browser"
            )
        )

        if browser_requested:
            if self.browser_adapter is None:
                context = self._prepare_context(
                    request,
                    initial_scene=None,
                    browser_page=None,
                    offer_workflow=None,
                    autonomous=autonomous,
                )
                context.requires_manual_review = True
                context.set_value(
                    "browser_observation_error",
                    "browser_adapter_unavailable",
                )
                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

            try:
                browser_page = self.browser_adapter.read()
            except Exception as exc:
                context = self._prepare_context(
                    request,
                    initial_scene=None,
                    browser_page=None,
                    offer_workflow=None,
                    autonomous=autonomous,
                )
                context.requires_manual_review = True
                context.set_value(
                    "browser_observation_error",
                    str(exc),
                )
                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

        if self.control_loop is not None:
            try:
                initial_scene = (
                    self.control_loop.observe_scene()
                )
            except Exception as exc:
                context = self._prepare_context(
                    request,
                    initial_scene=None,
                    offer_workflow=None,
                    autonomous=autonomous,
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

        learned_workflow_result = (
            self._try_execute_learned_workflow(
                request,
                initial_scene=initial_scene,
            )
        )

        if learned_workflow_result is not None:
            return learned_workflow_result

        # Detect intent without invoking the task reasoner a second time.
        # For the standard orchestrator this is deterministic and does not
        # execute anything. Custom orchestrators fall back to their returned
        # context when no explicit planner is exposed.
        detected_intent = None

        if hasattr(self.orchestrator, "planner"):
            detected_intent = (
                self.orchestrator.planner.plan(
                    request
                ).intent
            )

        if detected_intent is None:
            context = self._prepare_context(
                request,
                initial_scene=initial_scene,
                offer_workflow=None,
            )
            detected_intent = context.intent

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
                    offer_workflow_result,
                    continuation_of_offer=bool(
                        request.metadata.get(
                            "continuation_of_offer",
                            False,
                        )
                    ),
                )
            )

        # Prepare the final context only once for the standard path.
        context = self._prepare_context(
            request,
            initial_scene=initial_scene,
            browser_page=browser_page,
            offer_workflow=planning_offer_workflow,
            autonomous=autonomous,
        )

        if browser_page is not None:
            context.set_value(
                "browser_page",
                browser_page,
            )

        application_knowledge = getattr(
            self.orchestrator,
            "application_knowledge",
            None,
        )
        if application_knowledge is not None:
            context.set_value(
                "application_knowledge",
                application_knowledge,
            )

        # Preserve diagnostics in the context before any early-return path.
        # This makes a reasoning/manual-review decision explainable: the caller
        # can inspect the exact observed scene and parsed offer workflow instead
        # of seeing only the deterministic fallback plan.
        if initial_scene is not None:
            context.update_scene(initial_scene)

        task_planner = getattr(
            self.orchestrator,
            "task_planner",
            None,
        )
        proposal = getattr(
            task_planner,
            "last_proposal",
            None,
        )
        proposal_metadata = getattr(
            proposal,
            "metadata",
            {},
        )

        confirmation_token = request.metadata.get(
            "confirmation_token"
        )

        if confirmation_token is not None:
            if (
                not isinstance(confirmation_token, str)
                or not confirmation_token.strip()
            ):
                context.requires_manual_review = True
                context.set_value(
                    "task_reasoning_failure",
                    "invalid_confirmation_token",
                )
                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

            if (
                confirmation_token.strip()
                not in self._pending_confirmations
            ):
                context.requires_manual_review = True
                context.set_value(
                    "task_reasoning_failure",
                    "invalid_or_expired_confirmation_token",
                )
                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

        if isinstance(proposal_metadata, dict):
            resolved_external_knowledge = proposal_metadata.get(
                "external_knowledge"
            )
            if isinstance(resolved_external_knowledge, dict):
                context.set_value(
                    "external_knowledge",
                    resolved_external_knowledge,
                )

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

        reasoning_active = (
            getattr(
                self.orchestrator,
                "task_planner",
                None,
            )
            is not None
        )

        if (
            offer_workflow_result is not None
            and offer_workflow_result.requires_salesperson_input
        ):
            reasoning_gui_plan = (
                self.control_loop is not None
                and reasoning_active
                and self._is_gui_reasoning_plan(
                    context.plan,
                )
            )

            if not reasoning_gui_plan:
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

        if self.control_loop is not None:
            if self._consume_confirmation_token(
                request,
                context,
            ) is False and request.metadata.get(
                "confirmation_token"
            ) is not None:
                return AgentRuntimeResult(
                    intent=context.intent,
                    context=context,
                    execution_report=None,
                    requires_manual_review=True,
                    executed=False,
                )

            # Autonomous mode intentionally executes exactly one semantic
            # action per reasoning cycle. The next cycle observes the
            # resulting UI and reasons again instead of trusting a long
            # precomputed click sequence.
            if (
                autonomous
                and context.plan is not None
                and not context.plan.completed
                and context.plan.steps
            ):
                first_step = context.plan.steps[0]
                context.plan = ActionPlan(
                    intent=context.plan.intent,
                    steps=(
                        ActionStep(
                            index=1,
                            action=first_step.action,
                        ),
                    ),
                    confidence=context.plan.confidence,
                    requires_manual_review=(
                        context.plan.requires_manual_review
                    ),
                    completed=False,
                )

            control_loop_result = self.control_loop.run(
                plan=context.plan,
                context=context,
            )

            control_loop_requires_manual_review = bool(
                getattr(
                    control_loop_result,
                    "requires_manual_review",
                    False,
                )
            )
            control_loop_success = getattr(
                control_loop_result,
                "success",
                None,
            )
            if control_loop_success is None:
                control_loop_success = not control_loop_requires_manual_review

            self._remember_experience(
                kind="runtime_execution",
                application=(
                    initial_scene.observation.state.active_application
                    if initial_scene is not None
                    else None
                ),
                intent=context.intent.value,
                workflow_id=None,
                outcome=(
                    "manual_review"
                    if control_loop_requires_manual_review
                    else (
                        "success"
                        if control_loop_success
                        else "failure"
                    )
                ),
                summary=(
                    f"Executed semantic plan for intent "
                    f"'{context.intent.value}'."
                ),
                metadata={
                    "executed_actions": getattr(
                        control_loop_result,
                        "executed_actions",
                        0,
                    ),
                    "failed_actions": getattr(
                        control_loop_result,
                        "failed_actions",
                        0,
                    ),
                },
            )

            confirmation_request = (
                self._create_confirmation_request(
                    request,
                    context,
                    control_loop_result,
                )
            )

            return AgentRuntimeResult(
                intent=context.intent,
                context=context,
                execution_report=None,
                control_loop_result=control_loop_result,
                requires_manual_review=(
                    context.requires_manual_review
                    or control_loop_requires_manual_review
                ),
                executed=True,
                confirmation_request=confirmation_request,
            )

        execution_report = self.plan_executor.execute(
            plan=context.plan,
            context=context,
        )

        self._remember_experience(
            kind="runtime_execution",
            application=(
                initial_scene.observation.state.active_application
                if initial_scene is not None
                else None
            ),
            intent=context.intent.value,
            workflow_id=None,
            outcome=(
                "manual_review"
                if execution_report.requires_manual_review
                else (
                    "success"
                    if execution_report.success
                    else "failure"
                )
            ),
            summary=(
                f"Executed semantic plan for intent "
                f"'{context.intent.value}'."
            ),
            metadata={
                "steps": len(context.plan.steps),
            },
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

    def _remember_experience(
        self,
        *,
        kind: str,
        application: str | None,
        intent: str | None,
        workflow_id: str | None,
        outcome: str,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        store = getattr(
            self.orchestrator,
            "memory_store",
            None,
        )
        if store is None:
            return

        experience = AgentExperience(
            experience_id=f"{kind}:{uuid4().hex}",
            kind=kind,
            application=application,
            intent=intent,
            workflow_id=workflow_id,
            outcome=outcome,
            summary=summary,
            metadata=dict(metadata or {}),
        )

        store.add(experience)

    def run_autonomous(
        self,
        request: AgentRequest,
        *,
        max_steps: int = 30,
    ) -> AutonomousRunResult:
        """
        Run one user goal as a closed-loop autonomous session.

        Each cycle performs:
            observe -> reason -> one semantic action -> execute -> verify

        The next cycle starts from a fresh observation and can select a
        different action. The loop stops only on explicit completion,
        manual review/failure/stop, or the configured step limit.
        """
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")

        session_id = request.session_id or f"autonomous-{uuid4().hex}"
        autonomous_request = AgentRequest(
            message=request.message,
            session_id=session_id,
            salesman_id=request.salesman_id,
            metadata=dict(request.metadata),
            mode=request.mode,
        )

        results = []
        success = False
        completed = False
        requires_manual_review = False
        stopped = False
        reason = "step_limit_reached"

        for _ in range(max_steps):
            result = self.run(
                autonomous_request,
                autonomous=True,
            )
            results.append(result)

            resolved_external_knowledge = result.context.get_value(
                "external_knowledge"
            )

            if isinstance(resolved_external_knowledge, dict):
                autonomous_request = AgentRequest(
                    message=autonomous_request.message,
                    session_id=autonomous_request.session_id,
                    salesman_id=autonomous_request.salesman_id,
                    metadata={
                        **autonomous_request.metadata,
                        "external_knowledge": resolved_external_knowledge,
                    },
                    mode=autonomous_request.mode,
                )

            plan = result.context.plan
            if plan is not None and plan.completed:
                success = True
                completed = True
                reason = "task_completed_by_reasoner"
                break

            control = result.control_loop_result
            if control is None:
                requires_manual_review = True
                stopped = True
                reason = str(
                    result.context.get_value(
                        "task_reasoning_failure",
                        "runtime_stopped_before_control_loop",
                    )
                )
                break

            if control.requires_manual_review:
                requires_manual_review = True
                stopped = True
                reason = "control_loop_requires_manual_review"
                break

            if control.stopped:
                stopped = True
                reason = "control_loop_stopped"
                break

            if not control.success:
                stopped = True
                reason = "control_loop_failed"
                break

            if control.executed_actions == 0:
                stopped = True
                reason = "no_action_executed_without_completion"
                break
        else:
            stopped = True

        return AutonomousRunResult(
            session_id=session_id,
            step_results=tuple(results),
            success=success,
            completed=completed,
            requires_manual_review=requires_manual_review,
            stopped=stopped,
            reason=reason,
        )
