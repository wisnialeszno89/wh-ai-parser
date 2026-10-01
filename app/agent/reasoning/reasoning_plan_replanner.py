from app.agent.agent_action import AgentAction
from app.agent.planning.agent_action_normalizer import (
    AgentActionNormalizer,
)
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.planning.plan_replanner import (
    PlanReplanner,
)

from app.agent.perception.screen_scene_snapshot import (
    ScreenSceneSnapshot,
)

from app.agent.reasoning.plan_reasoner import (
    PlanReasoner,
)

from app.agent.reasoning.replanning_context import (
    ReplanningActionSnapshot,
    ReplanningContext,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


class ReasoningPlanReplanner(
    PlanReplanner
):
    """
    Adapter between the runtime replanning contract and
    the pluggable reasoning layer.
    """

    _FORBIDDEN_LOW_LEVEL_TERMS = (
        "pyautogui",
        "mouse_move",
        "mouse_click",
        "keyboard",
        "keypress",
        "key_press",
        "coordinate_click",
        "screen_coordinate",
        "window_handle",
        "runtime_id",
        "automation_id",
        "tracked_object_id",
    )

    def __init__(
        self,
        reasoner: PlanReasoner,
        action_normalizer: AgentActionNormalizer | None = None,
    ) -> None:
        self.reasoner = reasoner
        self.action_normalizer = (
            action_normalizer
            if action_normalizer is not None
            else AgentActionNormalizer()
        )

    def replan(
        self,
        *,
        plan: ActionPlan,
        failed_step: ActionStep,
        execution_result: ExecutionLoopResult,
        context: ExecutionContext,
    ) -> ActionPlan | None:

        attempt = execution_result.last_attempt

        if attempt is None:
            return None

        verification = (
            attempt.verification_result
        )

        if verification is None:
            return None

        scene = None

        if context.current_scene is not None:
            scene = (
                ScreenSceneSnapshot.from_scene(
                    context.current_scene
                )
            )

            scene = self._with_observation_metadata(
                scene,
                context,
            )

        replanning_context = (
            ReplanningContext(
                request_message=(
                    context.request.message
                ),
                intent=(
                    plan.intent.value
                ),
                active_plan=tuple(
                    ReplanningActionSnapshot(
                        name=step.action.name,
                        description=(
                            step.action.description
                        ),
                        requires_confirmation=(
                            step.action
                            .requires_confirmation
                        ),
                    )
                    for step in plan.steps
                ),
                failed_action_name=(
                    failed_step.action.name
                ),
                failed_action_description=(
                    failed_step.action.description
                ),
                attempt_number=(
                    attempt.attempt_number
                ),
                execution_success=(
                    attempt.execution_result.success
                ),
                execution_message=(
                    attempt.execution_result.message
                ),
                verification_verified=(
                    verification.verified
                ),
                verification_reason=(
                    verification.reason
                ),
                verification_confidence=(
                    verification.confidence
                ),
                verification_metadata=dict(
                    verification.metadata
                ),
                scene=scene,
                application_knowledge=(
                    context.get_value(
                        "application_knowledge"
                    )
                ),
            )
        )

        proposal = self.reasoner.reason(
            replanning_context
        )

        if proposal is None:
            return None

        if proposal.requires_manual_review:
            return None

        if not (
            0.0
            <= proposal.confidence
            <= 1.0
        ):
            return None

        if not proposal.actions:
            return None

        if not (
            proposal.actions
        ):
            return None

        actions = []

        for action in proposal.actions:
            if self._is_low_level(action.name) or (
                self._is_low_level(
                    action.description
                )
            ):
                return None

            if (
                action.target is not None
                and self._is_low_level(action.target)
            ):
                return None

            if (
                action.name.strip().casefold()
                in {"write_text", "type_text"}
                and (
                    not isinstance(action.target, str)
                    or not action.target.strip()
                    or not isinstance(action.value, str)
                    or not action.value
                )
            ):
                return None

            actions.append(
                self.action_normalizer.normalize(
                    AgentAction(
                        name=action.name,
                        description=action.description,
                        target=action.target,
                        value=action.value,
                        requires_confirmation=(
                            action.requires_confirmation
                        ),
                    )
                )
            )

        return ActionPlan(
            intent=plan.intent,
            steps=tuple(
                ActionStep(
                    index=index,
                    action=action,
                )
                for index, action
                in enumerate(
                    actions,
                    start=1,
                )
            ),
            confidence=proposal.confidence,
            requires_manual_review=(
                proposal.requires_manual_review
            ),
        )

    @classmethod
    def _is_low_level(
        cls,
        value: str,
    ) -> bool:
        normalized = (
            value.strip().casefold()
        )

        return any(
            term in normalized
            for term in cls._FORBIDDEN_LOW_LEVEL_TERMS
        )

    @staticmethod
    def _with_observation_metadata(
        scene: ScreenSceneSnapshot,
        context: ExecutionContext,
    ) -> ScreenSceneSnapshot:
        observation = context.last_observation

        if observation is None:
            return scene

        metadata = dict(
            scene.metadata
        )

        state = observation.state

        metadata.update(
            {
                "active_application": (
                    state.active_application
                ),
                "active_window_title": (
                    state.active_window_title
                ),
                "screen_width": (
                    state.screen_width
                ),
                "screen_height": (
                    state.screen_height
                ),
            }
        )

        return ScreenSceneSnapshot(
            elements=scene.elements,
            metadata=metadata,
        )
