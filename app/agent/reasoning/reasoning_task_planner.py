from app.agent.agent_intent import AgentIntent
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.agent_action import AgentAction

from app.agent.planning.agent_action_normalizer import (
    AgentActionNormalizer,
)
from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
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
        self.last_failure_reason: str | None = None
        self.last_proposal = None

    def plan(
        self,
        *,
        context: TaskPlanningContext,
    ) -> ActionPlan | None:
        self.last_failure_reason = None

        proposal = self.reasoner.reason(context)
        self.last_proposal = proposal

        reasoner_error = getattr(
            self.reasoner,
            "last_error",
            None,
        )

        if proposal is None:
            self.last_failure_reason = (
                reasoner_error
                or "reasoner_returned_no_proposal"
            )
            return None

        status = proposal.status.strip().casefold()

        if status not in {"continue", "done"}:
            self.last_failure_reason = "invalid_proposal_status"
            return None

        if proposal.requires_manual_review:
            self.last_failure_reason = (
                "provider_requested_manual_review"
            )
            return None

        if not 0.0 <= proposal.confidence <= 1.0:
            self.last_failure_reason = (
                "invalid_confidence"
            )
            return None

        if status == "done":
            if proposal.actions:
                self.last_failure_reason = "done_status_with_actions"
                return None

            return ActionPlan(
                intent=AgentIntent(context.intent),
                steps=(),
                confidence=proposal.confidence,
                requires_manual_review=False,
                completed=True,
            )

        if not proposal.actions:
            self.last_failure_reason = (
                "proposal_contains_no_actions"
            )
            return None

        actions = []

        for action in proposal.actions:
            if self._is_low_level(action.name):
                self.last_failure_reason = "low_level_action_name"
                return None

            if self._is_low_level(action.description):
                self.last_failure_reason = "low_level_action_description"
                return None

            if (
                action.target is not None
                and (
                    self._is_low_level(action.target)
                    or self._is_technical_target(action.target)
                )
            ):
                self.last_failure_reason = "low_level_or_technical_target"
                return None

            if (
                action.target is not None
                and context.scene is not None
                and not self._matches_visible_semantic_target(
                    action.target,
                    context.scene,
                )
            ):
                self.last_failure_reason = "target_not_visible_in_scene"
                return None

            if self._is_forbidden_offer_continuation_action(
                action,
                context,
            ):
                self.last_failure_reason = "forbidden_offer_continuation_action"
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
                self.last_failure_reason = "write_text_missing_target_or_value"
                return None

            normalized_action = self.action_normalizer.normalize(
                AgentAction(
                    name=action.name,
                    description=action.description,
                    requires_confirmation=(
                        action.requires_confirmation
                    ),
                    target=action.target,
                    value=action.value,
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
