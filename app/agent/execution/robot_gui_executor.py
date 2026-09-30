from app.agent.agent_action import AgentAction
from app.agent.execution.action_executor import ActionExecutor
from app.agent.execution.execution_result import ExecutionResult
from app.agent.perception.target_resolver import TargetResolver
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import RobotActionExecutor


class RobotGUIExecutor(ActionExecutor):
    """
    Agent-level adapter between semantic GUI actions and the
    universal robot execution layer.

    v1 supports:
        click_screen_element

    Target resolution is delegated to TargetResolver.
    """

    SUPPORTED_ACTIONS = {"click_screen_element"}

    def __init__(
        self,
        robot_action_executor: RobotActionExecutor,
        target_resolver: TargetResolver | None = None,
    ):
        self.robot_action_executor = robot_action_executor
        self.target_resolver = target_resolver or TargetResolver()

    def supports(self, action: AgentAction) -> bool:
        return action.name in self.SUPPORTED_ACTIONS

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        if action.name != "click_screen_element":
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Unsupported robot GUI action",
                requires_manual_review=True,
            )

        scene = context.current_scene
        if scene is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="No current screen scene available",
                requires_manual_review=True,
            )

        target = self._resolve_target(action, context)
        if target is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="No GUI target specified",
                requires_manual_review=True,
            )

        resolution = self.target_resolver.resolve(scene, target)

        if not resolution.resolved or resolution.element is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=resolution.reason,
                requires_manual_review=True,
                metadata={
                    "target": target,
                    "resolution_score": resolution.score,
                },
            )

        element = resolution.element

        target_id = self._tracked_object_id(element)

        if target_id is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Resolved screen element has no tracked object id",
                requires_manual_review=True,
                metadata={
                    "target": target,
                    "resolution_score": resolution.score,
                },
            )

        tracked_object = self._resolve_tracked_object(
            context,
            target_id,
        )

        if tracked_object is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Tracked object for resolved target was not found",
                requires_manual_review=True,
                metadata={
                    "target": target,
                    "target_id": target_id,
                    "resolution_score": resolution.score,
                },
            )

        root = context.get_value("gui_object_root")

        if root is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="GUI object root is unavailable",
                requires_manual_review=True,
                metadata={
                    "target": target,
                    "target_id": target_id,
                },
            )

        # The fused semantic element may have a provider-specific kind
        # (for example BUTTON from accessibility evidence) while the
        # underlying WindowHub tracked object remains an ICON. Verification
        # must validate the real tracked object, not a provider's display kind.
        expected_control_type = getattr(
            tracked_object,
            "control_type",
            self._control_type(element.kind),
        )
        interaction_capability_confidence = (
            self._interaction_capability_confidence(element)
        )

        result = self.robot_action_executor.execute(
            tracked_object=tracked_object,
            action=InteractionAction.CLICK,
            root=root,
            expected_control_type=expected_control_type,
            expected_bounds=tracked_object.object.bounds,
            interaction_capability=element.interaction_capability,
            interaction_capability_confidence=(
                interaction_capability_confidence
            ),
        )

        return ExecutionResult(
            action_name=action.name,
            success=result.success,
            message=result.reason,
            requires_manual_review=not result.success,
            metadata={
                "target": target,
                "target_id": target_id,
                "resolution_score": resolution.score,
                "point": result.point,
                "executed": result.executed,
                "control_type": element.kind,
                "interaction_capability": (
                    element.interaction_capability.value
                ),
                "interaction_capability_confidence": (
                    interaction_capability_confidence
                ),
            },
        )

    @staticmethod
    def _resolve_target(
        action: AgentAction,
        context: ExecutionContext,
    ) -> str | None:
        explicit = context.get_value("robot_target")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()

        explicit_id = context.get_value("robot_target_id")
        if isinstance(explicit_id, str) and explicit_id.strip():
            return explicit_id.strip()

        marker = action.description

        if "TO-" not in marker:
            return None

        start = marker.find("TO-")
        candidate = marker[start:].split()[0]

        return candidate or None

    @staticmethod
    def _tracked_object_id(element) -> str | None:
        metadata = element.metadata

        if not metadata:
            return None

        value = metadata.get("tracked_object_id")

        if isinstance(value, str) and value:
            return value

        return None

    @staticmethod
    def _interaction_capability_confidence(element) -> float | None:
        metadata = element.metadata or {}

        value = metadata.get(
            "interaction_capability_confidence"
        )

        if value is None:
            value = element.confidence

        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None

        return confidence

    @staticmethod
    def _resolve_tracked_object(
        context: ExecutionContext,
        target_id: str,
    ):
        tracked_objects = context.get_value("robot_tracked_objects")

        if not isinstance(tracked_objects, tuple):
            return None

        for tracked_object in tracked_objects:
            if tracked_object.id == target_id:
                return tracked_object

        return None

    @staticmethod
    def _control_type(value):
        from app.runtime.execution.vision.models.control_type import ControlType

        if isinstance(value, ControlType):
            return value

        if not isinstance(value, str):
            return ControlType.UNKNOWN

        normalized = value.strip().casefold()

        for control_type in ControlType:
            if control_type.value.casefold() == normalized:
                return control_type

        return ControlType.UNKNOWN
