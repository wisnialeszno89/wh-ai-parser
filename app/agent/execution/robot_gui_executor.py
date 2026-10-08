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
        write_text

    Target resolution is delegated to TargetResolver.
    """

    SUPPORTED_ACTIONS = {
        "click_screen_element",
        "write_text",
    }

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
        if action.name not in self.SUPPORTED_ACTIONS:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Unsupported robot GUI action",
                requires_manual_review=True,
            )

        if action.name == "write_text" and not isinstance(
            action.value,
            str,
        ):
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="write_text requires a text value",
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
                # An unresolved semantic target is outside the trusted
                # execution boundary. Do not guess or fall back to hardware.
                requires_manual_review=True,
                metadata={
                    "target": target,
                    "resolution_score": resolution.score,
                },
            )

        element = resolution.element

        target_id = self._tracked_object_id(element)

        if action.name == "write_text":
            target_id = None

        if target_id is None:
            if not self._is_guarded_uia_target(element):
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message=(
                        "Resolved screen element has no tracked object id "
                        "and is not a guarded UIA target"
                    ),
                    requires_manual_review=True,
                    metadata={
                        "target": target,
                        "resolution_score": resolution.score,
                    },
                )

            screen_origin = self._screen_origin(context)
            window_handle = self._window_handle(context)

            interaction = (
                InteractionAction.WRITE
                if action.name == "write_text"
                else InteractionAction.CLICK
            )

            result = self.robot_action_executor.execute_uia_screen_element(
                screen_element=element,
                action=interaction,
                text_value=action.value,
                screen_origin=screen_origin,
                window_handle=window_handle,
            )

            return ExecutionResult(
                action_name=action.name,
                success=result.success,
                message=result.reason,
                requires_manual_review=not result.success,
                metadata={
                    "target": target,
                    "target_id": result.target_id,
                    "resolution_score": resolution.score,
                    "point": result.point,
                    "screen_origin": screen_origin,
                    "window_handle": window_handle,
                    "executed": result.executed,
                    "execution_path": "uia_only",
                    "control_type": element.kind,
                    "interaction_capability": (
                        element.interaction_capability.value
                    ),
                    "interaction_capability_confidence": (
                        self._interaction_capability_confidence(element)
                    ),
                },
            )

        tracked_object = self._resolve_tracked_object(
            context,
            target_id,
        )

        # A fused target may carry a visual tracked-object id even when that
        # tracker has not reached the stability threshold required by the
        # physical tracked-object safety gate. When independent UIA evidence
        # is simultaneously strong, prefer the guarded UIA path instead of
        # failing solely because the visual tracker is still warming up.
        if (
            self._is_guarded_uia_target(element)
            and (
                tracked_object is None
                or self._tracked_object_is_unstable(tracked_object)
            )
        ):
            screen_origin = self._screen_origin(context)
            window_handle = self._window_handle(context)

            interaction = (
                InteractionAction.WRITE
                if action.name == "write_text"
                else InteractionAction.CLICK
            )

            result = self.robot_action_executor.execute_uia_screen_element(
                screen_element=element,
                action=interaction,
                text_value=action.value,
                screen_origin=screen_origin,
                window_handle=window_handle,
            )

            return ExecutionResult(
                action_name=action.name,
                success=result.success,
                message=result.reason,
                requires_manual_review=not result.success,
                metadata={
                    "target": target,
                    "target_id": result.target_id,
                    "resolution_score": resolution.score,
                    "point": result.point,
                    "screen_origin": screen_origin,
                    "window_handle": window_handle,
                    "executed": result.executed,
                    "execution_path": "uia_fallback_unstable_tracker",
                    "control_type": element.kind,
                    "interaction_capability": (
                        element.interaction_capability.value
                    ),
                    "interaction_capability_confidence": (
                        self._interaction_capability_confidence(element)
                    ),
                },
            )

        if tracked_object is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Tracked object for resolved target was not found",
                requires_manual_review=False,
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

        screen_origin = self._screen_origin(context)

        interaction = (
            InteractionAction.WRITE
            if action.name == "write_text"
            else InteractionAction.CLICK
        )

        result = self.robot_action_executor.execute(
            tracked_object=tracked_object,
            action=interaction,
            root=root,
            expected_control_type=expected_control_type,
            expected_bounds=tracked_object.object.bounds,
            interaction_capability=element.interaction_capability,
            interaction_capability_confidence=(
                interaction_capability_confidence
            ),
            screen_origin=screen_origin,
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
                "screen_origin": screen_origin,
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
    def _screen_origin(context: ExecutionContext) -> tuple[int, int] | None:
        observation = context.last_observation

        if observation is None:
            scene = context.current_scene
            observation = getattr(
                scene,
                "observation",
                None,
            )

        if observation is None:
            return None

        metadata = observation.metadata
        window_rect = metadata.get("window_rect")
        if window_rect is None:
            return None

        try:
            return (
                int(getattr(window_rect, "left")),
                int(getattr(window_rect, "top")),
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _window_handle(context: ExecutionContext) -> int | None:
        observation = context.last_observation

        if observation is None:
            scene = context.current_scene
            observation = getattr(
                scene,
                "observation",
                None,
            )

        if observation is None:
            return None

        # For LIVE UIA execution the foreground window is the safest
        # execution scope. WindowHub may put controls inside a modal child
        # window while the root application handle remains unchanged.
        value = observation.metadata.get(
            "foreground_window_handle",
            observation.metadata.get("window_handle"),
        )

        try:
            handle = int(value)
        except (TypeError, ValueError):
            return None

        return handle if handle > 0 else None

    @staticmethod
    def _is_guarded_uia_target(element) -> bool:
        metadata = element.metadata or {}

        return (
            metadata.get("source") in {
    "windowhub_ui_automation",
    "windows_ui_automation",
}
            and metadata.get("uia_enabled") is True
            and metadata.get("uia_visible") is True
            and isinstance(
                metadata.get("uia_runtime_id"),
                str,
            )
        )

    @staticmethod
    def _tracked_object_is_unstable(tracked_object) -> bool:
        try:
            return int(
                getattr(tracked_object, "consecutive_observations", 0)
            ) < 2
        except (TypeError, ValueError):
            return True

    @staticmethod
    def _resolve_target(
        action: AgentAction,
        context: ExecutionContext,
    ) -> str | None:
        action_target = getattr(action, "target", None)
        if isinstance(action_target, str) and action_target.strip():
            return action_target.strip()

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
