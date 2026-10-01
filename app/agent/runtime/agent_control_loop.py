from app.agent.decision.decision_engine import (
    DecisionEngine,
)

from app.agent.decision.decision_type import (
    DecisionType,
)

from app.agent.environment.environment_preparation_loop import (
    EnvironmentPreparationLoop,
)

from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.planning.plan_replanner import (
    PlanReplanner,
)

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.action_failure_policy import (
    ActionFailurePolicy,
)

from app.agent.runtime.action_step_result import (
    ActionStepResult,
)


from app.agent.runtime.action_step_lifecycle import (
    ActionStepLifecycle,
)

from app.agent.runtime.action_step_transition import (
    ActionStepTransition,
)


from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


from app.agent.runtime.action_step_runtime_state import (
    ActionStepRuntimeState,
)

from app.agent.runtime.action_plan_lifecycle import (
    ActionPlanLifecycle,
)

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)

from app.agent.runtime.control_loop_result import (
    ControlLoopResult,
)

from app.agent.runtime.action_failure_record import (
    ActionFailureRecord,
)

from app.agent.runtime.default_action_failure_policy import (
    DefaultActionFailurePolicy,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.verification_loop import (
    VerificationLoop,
)

from app.agent.runtime.plan_replan_record import (
    PlanReplanRecord,
)


class AgentControlLoop:
    """
    High-level controlled execution loop for an ActionPlan.

    Responsibilities:

    For every action in the plan:

    1. Prepare the environment when required.
    2. Observe the current environment.
    3. Perceive the semantic scene.
    4. Decide whether execution may proceed.
    5. Execute through VerificationLoop.
    6. Stop safely on failure or manual review.

    EnvironmentPreparationLoop owns the environment
    readiness feedback cycle.

    VerificationLoop owns the execution feedback cycle:

        execute
        ->
        observe
        ->
        perceive
        ->
        verify

    AgentControlLoop owns coordination across the
    complete plan.
    """

    def __init__(
        self,
        environment_runtime: EnvironmentRuntime,
        perception_engine: PerceptionEngine,
        decision_engine: DecisionEngine,
        verification_loop: VerificationLoop,
        environment_preparation_loop: (
            EnvironmentPreparationLoop | None
        ) = None,
        action_failure_policy: (
            ActionFailurePolicy | None
        ) = None,
        replanner: PlanReplanner | None = None,
        max_replans: int = 1,
    ) -> None:

        self.environment_runtime = (
            environment_runtime
        )

        self.perception_engine = (
            perception_engine
        )

        self.decision_engine = (
            decision_engine
        )

        self.verification_loop = (
            verification_loop
        )

        self.environment_preparation_loop = (
            environment_preparation_loop
        )

        self.action_failure_policy = (
            action_failure_policy
            if action_failure_policy is not None
            else DefaultActionFailurePolicy()
        )

        if max_replans < 0:
            raise ValueError(
                "max_replans must be non-negative."
            )

        self.replanner = replanner
        self.max_replans = max_replans

    def observe_scene(self) -> ScreenScene:
        """
        Observe and perceive the current environment without executing
        an action.

        This is the initial world-state snapshot used by the planner
        before it decides what should happen next.
        """

        observation = self.environment_runtime.observe()

        return self.perception_engine.perceive(
            observation
        )

    def run(
        self,
        plan: ActionPlan,
        context: ExecutionContext,
    ) -> ControlLoopResult:
        """
        Execute an action plan through the controlled
        agent loop.
        """

        plan_lifecycle = (
            ActionPlanLifecycle()
        )

        plan_lifecycle.transition_to(
            ActionPlanStatus.RUNNING
        )

        decisions = []

        execution_results = []

        failure_records = []

        replan_records = []

        step_results = []

        step_transitions = []

        runtime_states: dict[
            int,
            ActionStepRuntimeState,
        ] = {}

        def update_runtime_state(
            step_index: int,
            action_name: str,
            status: ActionStepStatus,
            attempts: int = 0,
            last_error: str = "",
        ) -> None:
            """
            Store the latest runtime state for one
            action step.
            """

            runtime_states[
                step_index
            ] = ActionStepRuntimeState(
                step_index=step_index,
                action_name=action_name,
                status=status,
                attempts=attempts,
                last_error=last_error,
            )

        def build_result(
            *,
            success: bool,
            requires_manual_review: bool = False,
            stopped: bool = False,
            plan_status: ActionPlanStatus | None = None,
        ) -> ControlLoopResult:
            """
            Build a complete immutable snapshot of the
            current control loop state.

            Every exit path must use this helper so the
            returned result always contains the complete
            execution history collected so far.
            
            if (
                not plan_lifecycle.is_finished
            ):

                if success:

                    target_status = (
                        ActionPlanStatus.COMPLETED
                    )

                elif requires_manual_review:

                    target_status = (
                        ActionPlanStatus.MANUAL_REVIEW
                    )

                elif stopped:

                    target_status = (
                        ActionPlanStatus.STOPPED
                    )

                else:

                    target_status = (
                        ActionPlanStatus.FAILED
                    )

                plan_lifecycle.transition_to(
                    target_status
                )

"""

            if (
                not plan_lifecycle.is_terminal
            ):

                if plan_status is not None:

                    target_status = plan_status

                elif requires_manual_review:

                    target_status = (
                        ActionPlanStatus.MANUAL_REVIEW
                    )

                elif success:

                    target_status = (
                        ActionPlanStatus.COMPLETED
                    )

                else:

                    target_status = (
                        ActionPlanStatus.FAILED
                    )

                plan_lifecycle.transition_to(
                    target_status
                )

            return ControlLoopResult(
                decisions=tuple(
                    decisions
                ),
                plan_status=(
                    plan_lifecycle.status
                ),
                plan_transitions=tuple(
                    plan_lifecycle.transitions
                ),
                execution_results=tuple(
                    execution_results
                ),
                step_results=tuple(
                    step_results
                ),
                step_transitions=tuple(
                    step_transitions
                ),
                runtime_states=tuple(
                    runtime_states.values()
                ),
                failure_records=tuple(
                    failure_records
                ),
                replan_records=tuple(
                    replan_records
                ),
                success=success,
                requires_manual_review=(
                    requires_manual_review
                ),
                stopped=stopped,
            )

        active_steps = list(plan.steps)
        active_plan = plan
        step_position = 0
        replan_count = 0
        next_replanned_step_index = (
            max(
                (
                    step.index
                    for step in active_steps
                ),
                default=0,
            )
            + 1
        )

        while step_position < len(
            active_steps
        ):

            step = active_steps[
                step_position
            ]

            action = step.action

            update_runtime_state(
                step.index,
                action.name,
                ActionStepStatus.PENDING,
            )

            lifecycle = (
                ActionStepLifecycle()
            )

            current_step_status = (
                ActionStepStatus.PENDING
            )

            def transition_step(
                target_status: ActionStepStatus,
            ) -> None:
                nonlocal current_step_status

                lifecycle.transition(
                    current_step_status,
                    target_status,
                )

                step_transitions.append(
                    ActionStepTransition(
                        action_name=action.name,
                        from_status=(
                            current_step_status
                        ),
                        to_status=(
                            target_status
                        ),
                    )
                )

                current_step_status = (
                    target_status
                )

                update_runtime_state(
                    step.index,
                    action.name,
                    current_step_status,
                )

            transition_step(
                ActionStepStatus.PREPARING
            )

            # ---------------------------------
            # 1. PREPARE ENVIRONMENT
            # ---------------------------------

            requirement = (
                action.environment_requirement
            )

            if (
                requirement is not None
                and self.environment_preparation_loop
                is not None
            ):

                preparation_result = (
                    self.environment_preparation_loop
                    .ensure_ready(
                        requirement
                    )
                )

                if not preparation_result.ready:

                    target_status = (
                        ActionStepStatus.MANUAL_REVIEW
                        if (
                            preparation_result
                            .execution_result
                            is not None
                            and preparation_result
                            .execution_result
                            .requires_user_action
                        )
                        else ActionStepStatus.STOPPED
                    )

                    transition_step(
                        target_status
                    )

                    step_results.append(
                        ActionStepResult(
                            action_name=action.name,
                            status=target_status,
                            reason=(
                                "Environment preparation "
                                "did not complete."
                            ),
                        )
                    )

                    execution_result = (
                        preparation_result
                        .execution_result
                    )

                    requires_manual_review = False

                    if (
                        execution_result is not None
                        and execution_result
                        .requires_user_action
                    ):
                        requires_manual_review = True

                    return build_result(
                        success=False,
                        requires_manual_review=(
                            requires_manual_review
                        ),
                        stopped=True,
                    )

            # ---------------------------------
            # 2. OBSERVE ENVIRONMENT
            # ---------------------------------
            #
            # Pure semantic/business actions do not mutate or depend on
            # the GUI. Avoid another expensive screenshot/UIA/vision cycle
            # for them. GUI actions explicitly opt into fresh perception.
            #
            # Keep the current scene untouched for logical actions so the
            # decision layer can still use the latest GUI evidence captured
            # before planning or by a previous GUI step.

            requires_environment_observation = (
                action.requires_environment_observation
                or action.name == "click_screen_element"
                or action.environment_requirement is not None
            )

            if requires_environment_observation:
                observation = (
                    self.environment_runtime.observe()
                )

                context.last_observation = (
                    observation
                )

                # ---------------------------------
                # 3. PERCEIVE ENVIRONMENT
                # ---------------------------------

                scene = (
                    self.perception_engine.perceive(
                        observation
                    )
                )

                context.update_scene(scene)

            # ---------------------------------
            # 4. DECIDE
            # ---------------------------------

            transition_step(
                ActionStepStatus.READY
            )

            decision = (
                self.decision_engine.decide(
                    action,
                    context,
                )
            )

            decisions.append(
                decision
            )

            # ---------------------------------
            # 5. HANDLE BLOCKERS
            # ---------------------------------

            if (
                decision.decision_type
                == DecisionType.MANUAL_REVIEW
            ):

                transition_step(
                    ActionStepStatus.MANUAL_REVIEW
                )

                step_results.append(
                    ActionStepResult(
                        action_name=action.name,
                        status=(
                            ActionStepStatus.MANUAL_REVIEW
                        ),
                        reason=(
                            "Decision requires "
                            "manual review."
                        ),
                    )
                )

                return build_result(
                    success=False,
                    requires_manual_review=True,
                    stopped=True,
                )

            if (
                decision.decision_type
                == DecisionType.STOP
            ):

                transition_step(
                    ActionStepStatus.STOPPED
                )

                step_results.append(
                    ActionStepResult(
                        action_name=action.name,
                        status=(
                            ActionStepStatus.STOPPED
                        ),
                        reason=(
                            "Decision stopped "
                            "execution."
                        ),
                    )
                )

                return build_result(
                    success=False,
                    stopped=True,
                    plan_status=(
                        ActionPlanStatus.STOPPED
                    ),
                )

            # ---------------------------------
            # 6. EXECUTE + VERIFY
            # ---------------------------------

            transition_step(
                ActionStepStatus.EXECUTING
            )

            execution_result = (
                self.verification_loop.run(
                    action,
                    context,
                )
            )

            execution_results.append(
                execution_result
            )

            update_runtime_state(
                step.index,
                action.name,
                current_step_status,
                attempts=len(
                    execution_result.attempts
                ),
            )

            # ---------------------------------
            # 7. HANDLE EXECUTION FAILURE
            # ---------------------------------

            if not execution_result.success:

                transition_step(
                    ActionStepStatus.FAILED
                )

                attempts = len(
                    execution_result.attempts
                )

                last_attempt = (
                    execution_result.last_attempt
                )

                reason = ""

                if (
                    last_attempt is not None
                    and last_attempt
                    .verification_result is not None
                    and not last_attempt
                    .verification_result
                    .verified
                ):
                    reason = (
                        last_attempt
                        .verification_result
                        .reason
                    )
                elif last_attempt is not None:
                    reason = (
                        last_attempt
                        .execution_result
                        .message
                    )

                verification_failed = (
                    last_attempt is not None
                    and last_attempt
                    .execution_result
                    .success
                    and last_attempt
                    .verification_result is not None
                    and not last_attempt
                    .verification_result
                    .verified
                )

                if (
                    verification_failed
                    and self.replanner is not None
                    and replan_count
                    < self.max_replans
                ):
                    replanned_plan = (
                        self.replanner.replan(
                            plan=active_plan,
                            failed_step=step,
                            execution_result=(
                                execution_result
                            ),
                            context=context,
                        )
                    )

                    if (
                        replanned_plan is not None
                        and replanned_plan.steps
                        and not (
                            replanned_plan
                            .requires_manual_review
                        )
                    ):
                        replacement_steps = []

                        for (
                            replanned_step
                        ) in replanned_plan.steps:
                            replacement_steps.append(
                                ActionStep(
                                    index=(
                                        next_replanned_step_index
                                    ),
                                    action=(
                                        replanned_step
                                        .action
                                    ),
                                )
                            )

                            next_replanned_step_index += 1

                        replacement_names = tuple(
                            replacement.action.name
                            for replacement
                            in replacement_steps
                        )

                        replan_count += 1

                        failure_records.append(
                            ActionFailureRecord(
                                action_name=action.name,
                                reason=reason,
                                attempts=attempts,
                                decision=(
                                    ActionFailureDecision
                                    .REPLAN
                                ),
                            )
                        )

                        replan_records.append(
                            PlanReplanRecord(
                                failed_action_name=(
                                    action.name
                                ),
                                reason=reason,
                                attempts=attempts,
                                replacement_actions=(
                                    replacement_names
                                ),
                            )
                        )

                        update_runtime_state(
                            step.index,
                            action.name,
                            current_step_status,
                            attempts=attempts,
                            last_error=reason,
                        )

                        step_results.append(
                            ActionStepResult(
                                action_name=action.name,
                                status=(
                                    ActionStepStatus.FAILED
                                ),
                                reason=(
                                    "Verification failed; "
                                    "plan was replanned."
                                ),
                                attempts=attempts,
                            )
                        )

                        active_steps[
                            step_position:
                        ] = replacement_steps

                        active_plan = (
                            ActionPlan(
                                intent=(
                                    replanned_plan
                                    .intent
                                ),
                                steps=tuple(
                                    replacement_steps
                                ),
                                confidence=(
                                    replanned_plan
                                    .confidence
                                ),
                                requires_manual_review=(
                                    replanned_plan
                                    .requires_manual_review
                                ),
                            )
                        )

                        continue

                failure_decision = (
                    self.action_failure_policy.decide(
                        action,
                        execution_result,
                        context,
                    )
                )

                failure_record = (
                    ActionFailureRecord(
                        action_name=action.name,
                        reason=reason,
                        attempts=attempts,
                        decision=failure_decision,
                    )
                )

                failure_records.append(
                    failure_record
                )

                update_runtime_state(
                    step.index,
                    action.name,
                    current_step_status,
                    attempts=attempts,
                    last_error=reason,
                )

                if (
                    failure_decision
                    == ActionFailureDecision.CONTINUE
                ):

                    step_results.append(
                        ActionStepResult(
                            action_name=action.name,
                            status=(
                                ActionStepStatus.FAILED
                            ),
                            reason=reason,
                            attempts=attempts,
                        )
                    )

                    step_position += 1
                    continue

                if (
                    failure_decision
                    == ActionFailureDecision.SKIP
                ):

                    transition_step(
                        ActionStepStatus.SKIPPED
                    )

                    step_results.append(
                        ActionStepResult(
                            action_name=action.name,
                            status=(
                                ActionStepStatus.SKIPPED
                            ),
                            reason=reason,
                            attempts=attempts,
                        )
                    )

                    step_position += 1
                    continue

                if (
                    failure_decision
                    == ActionFailureDecision.MANUAL_REVIEW
                ):

                    transition_step(
                        ActionStepStatus.MANUAL_REVIEW
                    )

                    step_results.append(
                        ActionStepResult(
                            action_name=action.name,
                            status=(
                                ActionStepStatus.MANUAL_REVIEW
                            ),
                            reason=reason,
                            attempts=attempts,
                        )
                    )

                    return build_result(
                        success=False,
                        requires_manual_review=True,
                        stopped=True,
                    )

                step_results.append(
                    ActionStepResult(
                        action_name=action.name,
                        status=(
                            ActionStepStatus.STOPPED
                        ),
                        reason=reason,
                        attempts=attempts,
                    )
                )

                return build_result(
                    success=False,
                    requires_manual_review=(
                        execution_result
                        .requires_manual_review
                    ),
                    stopped=True,
                )

            transition_step(
                ActionStepStatus.VERIFYING
            )

            transition_step(
                ActionStepStatus.COMPLETED
            )

            step_results.append(
                ActionStepResult(
                    action_name=action.name,
                    status=(
                        ActionStepStatus.COMPLETED
                    ),
                    attempts=len(
                        execution_result.attempts
                    ),
                )
            )

            if (
                execution_result
                .requires_manual_review
            ):

                step_results.append(
                    ActionStepResult(
                        action_name=action.name,
                        status=(
                            ActionStepStatus.MANUAL_REVIEW
                        ),
                        reason="Execution requires manual review.",
                        attempts=len(
                            execution_result.attempts
                        ),
                    )
                )

                return build_result(
                    success=False,
                    requires_manual_review=True,
                    stopped=True,
                )

            step_position += 1

        return build_result(
            success=True,
        )
