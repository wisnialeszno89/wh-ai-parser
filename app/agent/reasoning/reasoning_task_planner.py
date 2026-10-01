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
                and (
                    self._is_low_level(action.target)
                    or self._is_technical_target(action.target)
                )
            ):
                return None

            if (
                action.target is not None
                and context.scene is not None
                and not self._matches_visible_semantic_target(
                    action.target,
                    context.scene,
                )
            ):
                return None

            if self._is_forbidden_offer_continuation_action(
                action,
                context,
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


    @staticmethod
    def _is_forbidden_offer_continuation_action(
        action: ReasoningAction,
        context: TaskPlanningContext,
    ) -> bool:
        workflow = context.offer_workflow or {}

        if (
            workflow.get("workflow_state")
            != "ready_for_pricing"
            or not workflow.get("continuation_of_offer")
        ):
            return False

        if action.name.strip().casefold() == "open_new_offer":
            return True

        target = (
            action.target.strip().casefold()
            if isinstance(action.target, str)
            else ""
        )

        return target in {
            "nowa oferta",
            "nowa_oferta",
        }

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


    @staticmethod
    def _matches_visible_semantic_target(
        target: str,
        scene,
    ) -> bool:
        normalized = target.strip().casefold()

        if not normalized:
            return False

        for element in scene.elements:
            values = [element.label]

            metadata = element.metadata or {}
            values.extend(
                metadata.get(key)
                for key in (
                    "name",
                    "semantic_label",
                    "description",
                    "role",
                )
            )

            for value in values:
                if (
                    isinstance(value, str)
                    and value.strip().casefold()
                    == normalized
                ):
                    return True

        return False


    @staticmethod
    def _is_technical_target(value: str) -> bool:
        normalized = value.strip().casefold()

        if not normalized:
            return False

        prefixes = (
            "idc_",
            "uia:",
            "automationid:",
            "automation_id=",
            "runtimeid:",
            "runtime_id=",
            "tracked_object:",
            "tracked_object_id=",
        )

        return normalized.startswith(prefixes)
