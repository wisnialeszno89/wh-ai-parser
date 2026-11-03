from collections.abc import Mapping

from app.agent.agent_action import AgentAction
from app.agent.execution.action_executor import ActionExecutor
from app.agent.execution.execution_result import ExecutionResult
from app.agent.perception.target_resolver import TargetResolver
from app.agent.perception.semantic_target_query import SemanticTargetQuery
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
        "press_key",
        "activate_window",
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

        if action.name == "press_key":
            if not isinstance(action.value, str) or not action.value:
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="press_key requires an allowlisted key sequence",
                    requires_manual_review=True,
                )

            if context.current_scene is None:
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="No current screen scene available",
                    requires_manual_review=True,
                )

            window_handle = self._window_handle(context)
            result = self.robot_action_executor.execute_keyboard_input(
                sequence=action.value,
                window_handle=window_handle,
            )
            return ExecutionResult(
                action_name=action.name,
                success=result.success,
                message=result.reason,
                requires_manual_review=not result.success,
                metadata={
                    "target": None,
                    "window_handle": window_handle,
                    "executed": result.executed,
                    "execution_path": "keyboard_input",
                    "key_sequence": action.value,
                },
            )

        if action.name == "activate_window":
            if not isinstance(action.value, str) or not action.value.isdigit():
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="activate_window requires a locally bound window handle",
                    requires_manual_review=True,
                )

            scene = context.current_scene
            if scene is None:
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="No current desktop scene available",
                    requires_manual_review=True,
                )

            observation = context.last_observation or scene.observation
            metadata = observation.metadata
            inventory = metadata.get("desktop_windows", ())
            observed_handles = []
            for window in inventory if isinstance(inventory, (tuple, list)) else ():
                candidate = getattr(window, "handle", None)
                if (
                    isinstance(candidate, int)
                    and not isinstance(candidate, bool)
                    and candidate > 0
                ):
                    observed_handles.append(candidate)

            target_handle = int(action.value)
            foreground_handle = metadata.get(
                "foreground_window_handle",
                metadata.get("window_handle"),
            )
            if isinstance(foreground_handle, bool):
                foreground_handle = 0
            else:
                try:
                    foreground_handle = int(foreground_handle)
                except (TypeError, ValueError, OverflowError):
                    foreground_handle = 0

            local_binding = context.get_value(
                "_computer_use_v2_window_activation_binding"
            )
            if (
                not isinstance(local_binding, Mapping)
                or local_binding.get("window_handle") != target_handle
                or local_binding.get("label") != action.target
                or local_binding.get("foreground_window_handle") != foreground_handle
                or not isinstance(local_binding.get("target_ref"), str)
            ):
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="No matching V2-local window activation binding",
                    requires_manual_review=True,
                    metadata={"target": action.target, "executed": False},
                )

            if (
                foreground_handle <= 0
                or target_handle == foreground_handle
                or target_handle not in observed_handles
            ):
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message="Target window is not an inactive member of the latest desktop inventory",
                    requires_manual_review=True,
                    metadata={"target": action.target, "executed": False},
                )

            result = self.robot_action_executor.execute_window_activation(
                window_handle=target_handle,
                expected_foreground_handle=foreground_handle,
                observed_window_handles=tuple(observed_handles),
            )
            return ExecutionResult(
                action_name=action.name,
                success=result.success,
                message=result.reason,
                requires_manual_review=not result.success,
                metadata={
                    "target": action.target,
                    "window_handle": target_handle,
                    "executed": result.executed,
                    "execution_path": "desktop_window_activation",
                },
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
        target_label = (
            target.description
            if isinstance(target, SemanticTargetQuery)
            else target
        )

        if not resolution.resolved or resolution.element is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=resolution.reason,
                # Ambiguous/missing semantic targets are recoverable execution
                # failures. The control loop may retry, replan, or skip an
                # explicitly optional action. Safety-gate failures remain
                # manual-review conditions later in this executor.
                requires_manual_review=False,
                metadata={
                    "target": target_label,
                    "resolution_score": resolution.score,
                },
            )

        element = resolution.element

        element_source = (element.metadata or {}).get("source")
        if (
            element_source in {
                "windows_ui_automation",
                "windowhub_ui_automation",
            }
            and not self._has_unique_uia_target_identity(scene, element)
        ):
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="UIA target identity is missing or ambiguous.",
                requires_manual_review=True,
                metadata={
                    "target": target_label,
                    "resolution_score": resolution.score,
                    "executed": False,
                },
            )

        target_id = self._tracked_object_id(element)

        if action.name == "write_text":
            target_id = None

        if target_id is None:
            if (
                not self._is_uia_only_target(element)
                or not self._has_unique_uia_target_identity(scene, element)
            ):
                return ExecutionResult(
                    action_name=action.name,
                    success=False,
                    message=(
                        "Resolved screen element has no tracked object id "
                        "and is not a guarded UIA target"
                    ),
                    requires_manual_review=False,
                    metadata={
                        "target": target_label,
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
                    "target": target_label,
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

        if tracked_object is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Tracked object for resolved target was not found",
                requires_manual_review=False,
                metadata={
                    "target": target_label,
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
                    "target": target_label,
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
                "target": target_label,
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

        value = observation.metadata.get("window_handle")

        try:
            handle = int(value)
        except (TypeError, ValueError):
            return None

        return handle if handle > 0 else None

    @staticmethod
    def _is_uia_only_target(element) -> bool:
        metadata = element.metadata or {}

        source = metadata.get("source")
        return (
            isinstance(source, str)
            and source in {
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
    def _has_unique_uia_target_identity(scene, element) -> bool:
        metadata = element.metadata or {}
        runtime_id = metadata.get("uia_runtime_id")
        source = metadata.get("source")
        if (
            source not in {
                "windowhub_ui_automation",
                "windows_ui_automation",
            }
            or not isinstance(runtime_id, str)
            or not runtime_id.strip()
            or not any(candidate is element for candidate in scene.elements)
        ):
            return False

        matches = 0
        for candidate in scene.elements:
            candidate_metadata = candidate.metadata or {}
            if (
                candidate_metadata.get("source") in {
                    "windowhub_ui_automation",
                    "windows_ui_automation",
                }
                and candidate_metadata.get("uia_runtime_id") == runtime_id
            ):
                matches += 1
                if matches > 1:
                    return False
        return matches == 1

    @staticmethod
    def _resolve_target(
        action: AgentAction,
        context: ExecutionContext,
    ) -> str | SemanticTargetQuery | None:
        action_target = getattr(action, "target", None)
        if isinstance(action_target, SemanticTargetQuery):
            return action_target
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
