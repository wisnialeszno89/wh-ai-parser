from app.agent.agent_intent import AgentIntent
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.agent_action import AgentAction

from app.agent.planning.agent_action_normalizer import (
    AgentActionNormalizer,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)
from app.agent.reasoning.task_reasoner import (
    TaskReasoner,
)


class ReasoningTaskPlanner:
    """
    Converts a TaskReasoner proposal into an ActionPlan.

    The adapter is the safety boundary between model-generated
    semantic planning and the rest of the runtime.
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
        reasoner: TaskReasoner,
        action_normalizer: AgentActionNormalizer | None = None,
    ) -> None:
        self.reasoner = reasoner
        self.action_normalizer = (
            action_normalizer
            if action_normalizer is not None
            else AgentActionNormalizer()
        )

    def plan(
        self,
        *,
        context: TaskPlanningContext,
    ) -> ActionPlan | None:
        proposal = self.reasoner.reason(context)

        if proposal is None:
            return None

        if proposal.requires_manual_review:
            return None

        if not 0.0 <= proposal.confidence <= 1.0:
            return None

        if not proposal.actions:
            return None

        actions = []

        for action in proposal.actions:
            if self._is_low_level(action.name):
                return None

            if self._is_low_level(action.description):
                return None

            if (
                action.target is not None
                and self._is_low_level(action.target)
            ):
                return None

            normalized_action = self.action_normalizer.normalize(
                AgentAction(
                    name=action.name,
                    description=action.description,
                    requires_confirmation=(
                        action.requires_confirmation
                    ),
                    target=action.target,
                )
            )

            actions.append(
                normalized_action
            )

        return ActionPlan(
            intent=AgentIntent(context.intent),
            steps=tuple(
                ActionStep(
                    index=index,
                    action=action,
                )
                for index, action in enumerate(
                    actions,
                    start=1,
                )
            ),
            confidence=proposal.confidence,
            requires_manual_review=False,
        )

    @classmethod
    def _is_low_level(
        cls,
        value: str,
    ) -> bool:
        normalized = value.strip().casefold()

        return any(
            term in normalized
            for term in cls._FORBIDDEN_LOW_LEVEL_TERMS
        )
