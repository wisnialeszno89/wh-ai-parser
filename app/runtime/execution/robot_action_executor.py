from dataclasses import dataclass
from enum import Enum

from app.runtime.execution.action_policy import ActionPolicy
from app.runtime.execution.action_result import ActionResult
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)
from app.runtime.execution.verification import ExecutionVerifier
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.bridges.execution_safety_gate import ExecutionSafetyGate
from app.runtime.execution.vision.bridges.tracked_object_gui_bridge import TrackedObjectGUIBridge


class RobotExecutionMode(Enum):
    DRY_RUN = "dry_run"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class RobotActionResult:
    success: bool
    action: InteractionAction
    mode: RobotExecutionMode
    executed: bool
    target_id: str | None = None
    point: tuple[int, int] | None = None
    confidence: float = 0.0
    reason: str = ""
    action_result: ActionResult | None = None


class RobotActionExecutor:
    """
    Universal robot action executor.

    Pipeline:
        SafetyGate
            -> GUI Bridge
            -> target point
            -> RobotMouse

    RobotMouse is the only hardware adapter used by this executor.
    """

    def __init__(
        self,
        *,
        mode: RobotExecutionMode = RobotExecutionMode.DRY_RUN,
        safety_gate=None,
        bridge=None,
        mouse=None,
        action_policy=None,
        verifier=None,
        keyboard=None,
    ):
        self.mode = mode
        self.action_policy = action_policy or ActionPolicy()
        self.safety_gate = safety_gate or ExecutionSafetyGate()
        self.verifier = verifier or ExecutionVerifier()
        self.bridge = bridge or TrackedObjectGUIBridge()

        mouse_mode = (
            RobotMouseMode.DRY_RUN
            if mode is RobotExecutionMode.DRY_RUN
            else RobotMouseMode.LIVE
        )
        self.mouse = mouse or RobotMouse(mode=mouse_mode)
        self.keyboard = keyboard or KeyboardController()

    def execute(
        self,
        *,
        tracked_object,
        action,
        root,
        expected_control_type: ControlType | None = None,
        expected_bounds: Rect | None = None,
        interaction_capability=None,
        interaction_capability_confidence: float | None = None,
        screen_origin: tuple[int, int] | None = None,
    ) -> RobotActionResult:

        if not self.action_policy.can_execute(action):
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._target_id(tracked_object),
                confidence=self._confidence(tracked_object),
                reason="Action policy rejected action",
            )

        safety_gate_kwargs = {}

        if (
            interaction_capability is not None
            or interaction_capability_confidence is not None
        ):
            safety_gate_kwargs = {
                "interaction_capability": interaction_capability,
                "interaction_capability_confidence": (
                    interaction_capability_confidence
                ),
            }

        if not self.safety_gate.can_execute(
            tracked_object,
            action,
            **safety_gate_kwargs,
        ):
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._target_id(tracked_object),
                confidence=self._confidence(tracked_object),
                reason="Safety gate rejected action",
            )

        target = self.bridge.resolve(tracked_object, root)

        if target is None:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                confidence=self._confidence(tracked_object),
                reason="Tracked object could not be resolved to GUIObject",
            )

        local_point = self._center(target)
        target_id = getattr(target, "id", None)
        confidence = self._confidence(tracked_object)

        if self.mode is RobotExecutionMode.LIVE and screen_origin is None:
            return RobotActionResult(
                success=False,
                action=action,
                mode=self.mode,
                executed=False,
                target_id=target_id,
                point=local_point,
                confidence=confidence,
                reason="LIVE execution requires a known screen origin",
            )

        origin = screen_origin or (0, 0)
        point = (
            local_point[0] + origin[0],
            local_point[1] + origin[1],
        )

        if (
            expected_control_type is not None
            and expected_bounds is not None
        ):
            verification = self.verifier.verify(
                tracked_object=tracked_object,
                expected_control_type=expected_control_type,
                expected_bounds=expected_bounds,
            )

            if not verification.verified:
                return RobotActionResult(
                    success=False,
                    action=action,
                    mode=self.mode,
                    executed=False,
                    target_id=target_id,
                    point=point,
                    confidence=confidence,
                    reason=(
                        f"Verification failed: "
                        f"{verification.reason}"
                    ),
                )

        if action is not InteractionAction.CLICK:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=target_id,
                point=point,
                confidence=confidence,
                reason=f"Action {action.value} is not supported by RobotActionExecutor v1",
            )

        mouse_result = self.mouse.click(*point)

        if self.mode is RobotExecutionMode.LIVE and not mouse_result.executed:
            return RobotActionResult(
                success=False,
                action=action,
                mode=self.mode,
                executed=False,
                target_id=target_id,
                point=mouse_result.point,
                confidence=confidence,
                reason="LIVE execution is not enabled",
            )

        return RobotActionResult(
            success=mouse_result.success,
            action=action,
            mode=self.mode,
            executed=mouse_result.executed,
            target_id=target_id,
            point=mouse_result.point,
            confidence=confidence,
            reason=mouse_result.reason,
        )


    def execute_uia_screen_element(
        self,
        *,
        screen_element,
        action,
        text_value: str | None = None,
        screen_origin: tuple[int, int] | None = None,
        window_handle=None,
    ) -> RobotActionResult:
        """
        Execute a click against a semantic UI Automation element.

        This is the explicit UIA-only path used when accessibility evidence
        is strong enough to identify an interactive WindowHub control but
        visual tracking cannot provide a stable tracked-object id.
        """

        if not self.action_policy.can_execute(action):
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                reason="Action policy rejected action",
            )

        if action not in {
            InteractionAction.CLICK,
            InteractionAction.WRITE,
        }:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                reason=(
                    f"Action {action.value} is not supported by "
                    "RobotActionExecutor UIA path"
                ),
            )

        metadata = getattr(screen_element, "metadata", None) or {}
        confidence = self._screen_element_confidence(screen_element)

        if action is InteractionAction.WRITE:
            if not isinstance(text_value, str) or not text_value:
                return RobotActionResult(
                    False,
                    action,
                    self.mode,
                    False,
                    target_id=self._uia_target_id(metadata),
                    confidence=confidence,
                    reason="WRITE requires a non-empty text value",
                )

            control_type = str(
                metadata.get("uia_control_type", "")
            ).strip().casefold()

            if control_type not in {
                "edit",
                "combobox",
            }:
                return RobotActionResult(
                    False,
                    action,
                    self.mode,
                    False,
                    target_id=self._uia_target_id(metadata),
                    confidence=confidence,
                    reason=(
                        "WRITE target is not an editable UIA control"
                    ),
                )
        capability = getattr(
            screen_element,
            "interaction_capability",
            None,
        )

        if not self.safety_gate.can_execute_uia_element(
            metadata=metadata,
            interaction_capability=capability,
            interaction_capability_confidence=(
                metadata.get(
                    "interaction_capability_confidence",
                    confidence,
                )
            ),
            window_handle=window_handle,
            require_foreground=(
                self.mode is RobotExecutionMode.LIVE
            ),
        ):
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._uia_target_id(metadata),
                confidence=confidence,
                reason="UIA safety gate rejected action",
            )

        x = getattr(screen_element, "x", None)
        y = getattr(screen_element, "y", None)
        width = getattr(screen_element, "width", None)
        height = getattr(screen_element, "height", None)

        if not all(
            isinstance(value, int)
            for value in (x, y, width, height)
        ):
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._uia_target_id(metadata),
                confidence=confidence,
                reason="UIA target has no valid bounds",
            )

        if width <= 0 or height <= 0:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._uia_target_id(metadata),
                confidence=confidence,
                reason="UIA target bounds are non-positive",
            )

        if self.mode is RobotExecutionMode.LIVE and screen_origin is None:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._uia_target_id(metadata),
                confidence=confidence,
                reason="LIVE UIA execution requires a known screen origin",
            )

        origin = screen_origin or (0, 0)
        point = (
            int(x + width // 2 + origin[0]),
            int(y + height // 2 + origin[1]),
        )

        if self.mode is RobotExecutionMode.LIVE:
            live_result = self._execute_live_uia_target(
                metadata=metadata,
                action=action,
                text_value=text_value,
                window_handle=window_handle,
                fallback_point=point,
                confidence=confidence,
            )
            if live_result is not None:
                return live_result

        mouse_result = self.mouse.click(*point)

        if self.mode is RobotExecutionMode.LIVE and not mouse_result.executed:
            return RobotActionResult(
                False,
                action,
                self.mode,
                False,
                target_id=self._uia_target_id(metadata),
                point=mouse_result.point,
                confidence=confidence,
                reason="LIVE UIA execution was not performed",
            )

        if action is InteractionAction.WRITE:
            if not mouse_result.success:
                return RobotActionResult(
                    False,
                    action,
                    self.mode,
                    mouse_result.executed,
                    target_id=self._uia_target_id(metadata),
                    point=mouse_result.point,
                    confidence=confidence,
                    reason=mouse_result.reason,
                )

            if self.mode is RobotExecutionMode.DRY_RUN:
                return RobotActionResult(
                    True,
                    action,
                    self.mode,
                    False,
                    target_id=self._uia_target_id(metadata),
                    point=mouse_result.point,
                    confidence=confidence,
                    reason="DRY_RUN text entry; hardware not touched",
                )

            try:
                self.keyboard.hotkey("ctrl", "a")
                self.keyboard.write(text_value)
            except Exception as exc:
                return RobotActionResult(
                    False,
                    action,
                    self.mode,
                    False,
                    target_id=self._uia_target_id(metadata),
                    point=mouse_result.point,
                    confidence=confidence,
                    reason=f"LIVE text entry failed: {exc}",
                )

            return RobotActionResult(
                True,
                action,
                self.mode,
                True,
                target_id=self._uia_target_id(metadata),
                point=mouse_result.point,
                confidence=confidence,
                reason="LIVE text entered via keyboard",
            )

        return RobotActionResult(
            success=mouse_result.success,
            action=action,
            mode=self.mode,
            executed=mouse_result.executed,
            target_id=self._uia_target_id(metadata),
            point=mouse_result.point,
            confidence=confidence,
            reason=mouse_result.reason,
        )

    def _execute_live_uia_target(
        self,
        *,
        metadata,
        action,
        text_value: str | None,
        window_handle,
        fallback_point: tuple[int, int],
        confidence: float,
    ) -> RobotActionResult | None:
        """
        Prefer the live UI Automation control itself over a calculated
        screen coordinate.

        This is important for modal controls such as radio buttons: the
        semantic target is reacquired from the current foreground WindowHub
        window immediately before the action, so a stale/incorrect
        center point cannot silently hit an adjacent option.
        """
        if __import__("os").name != "nt":
            return None

        try:
            handle = int(window_handle)
        except (TypeError, ValueError):
            return None

        if handle <= 0:
            return None

        runtime_id = metadata.get("uia_runtime_id")
        target_name = metadata.get("name")
        control_type = metadata.get("uia_control_type")

        try:
            from pywinauto import Desktop

            window = Desktop(backend="uia").window(
                handle=handle
            ).wrapper_object()

            candidates = []
            for item in window.descendants():
                try:
                    item_runtime_id = self._normalize_uia_runtime_id(
                        getattr(item.element_info, "runtime_id", None)
                    )
                    item_control_type = str(
                        getattr(
                            item.element_info,
                            "control_type",
                            "",
                        )
                    ).strip().casefold()
                    item_name = str(
                        getattr(
                            item.element_info,
                            "name",
                            "",
                        )
                    ).strip()
                except Exception:
                    continue

                if (
                    isinstance(runtime_id, str)
                    and runtime_id
                    and item_runtime_id == runtime_id
                ):
                    candidates.append(item)
                    continue

                if (
                    not runtime_id
                    and isinstance(target_name, str)
                    and target_name.strip()
                    and item_name.casefold()
                    == target_name.strip().casefold()
                    and (
                        not isinstance(control_type, str)
                        or not control_type.strip()
                        or item_control_type
                        == control_type.strip().casefold()
                    )
                ):
                    candidates.append(item)

            if len(candidates) != 1:
                return None

            target = candidates[0]

            # Prefer the UIA semantic interaction pattern over a coordinate
            # click. Radio buttons and other SelectionItem controls must be
            # selected through their control pattern; buttons can expose the
            # Invoke pattern. This is more reliable than clicking the center
            # of a small modal control.
            used_semantic_pattern = False
            normalized_type = (
                control_type.strip().casefold()
                if isinstance(control_type, str)
                else ""
            )

            if normalized_type in {
                "radiobutton",
                "listitem",
                "tabitem",
                "treeitem",
            }:
                select = getattr(target, "select", None)
                if callable(select):
                    select()
                    used_semantic_pattern = True

            if not used_semantic_pattern and normalized_type in {
                "button",
                "splitbutton",
                "menuitem",
                "hyperlink",
            }:
                invoke = getattr(target, "invoke", None)
                if callable(invoke):
                    invoke()
                    used_semantic_pattern = True

            if not used_semantic_pattern and normalized_type == "checkbox":
                toggle = getattr(target, "toggle", None)
                if callable(toggle):
                    toggle()
                    used_semantic_pattern = True

            if not used_semantic_pattern:
                click_input = getattr(target, "click_input", None)
                if not callable(click_input):
                    return None
                click_input()

            if action is InteractionAction.WRITE:
                if not isinstance(text_value, str) or not text_value:
                    return RobotActionResult(
                        False,
                        action,
                        self.mode,
                        False,
                        target_id=self._uia_target_id(metadata),
                        point=fallback_point,
                        confidence=confidence,
                        reason="WRITE requires a non-empty text value",
                    )

                try:
                    self.keyboard.hotkey("ctrl", "a")
                    self.keyboard.write(text_value)
                except Exception as exc:
                    return RobotActionResult(
                        False,
                        action,
                        self.mode,
                        False,
                        target_id=self._uia_target_id(metadata),
                        point=fallback_point,
                        confidence=confidence,
                        reason=f"LIVE text entry failed: {exc}",
                    )

            return RobotActionResult(
                True,
                action,
                self.mode,
                True,
                target_id=self._uia_target_id(metadata),
                point=fallback_point,
                confidence=confidence,
                reason="LIVE UIA control executed directly",
            )

        except Exception:
            return None

    @staticmethod
    def _normalize_uia_runtime_id(value) -> str | None:
        if value is None:
            return None

        if isinstance(value, (tuple, list)):
            return "-".join(str(part) for part in value)

        return str(value)

    @staticmethod
    def _screen_element_confidence(screen_element) -> float:
        try:
            return float(
                getattr(screen_element, "confidence", 0.0)
                or 0.0
            )
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _uia_target_id(metadata) -> str | None:
        value = metadata.get("provider_element_id")
        if isinstance(value, str) and value:
            return value

        value = metadata.get("uia_runtime_id")
        if isinstance(value, str) and value:
            return value

        value = metadata.get("automation_id")
        if isinstance(value, str) and value:
            return f"uia:auto:{value}"

        return None

    @staticmethod
    def _center(target) -> tuple[int, int]:
        bounds = getattr(target, "bounds", None)

        if bounds is None:
            raise ValueError("Target GUIObject has no bounds")

        return (
            bounds.x + bounds.width // 2,
            bounds.y + bounds.height // 2,
        )

    @staticmethod
    def _confidence(tracked_object) -> float:
        return float(getattr(tracked_object, "confidence", 0.0))

    @staticmethod
    def _target_id(tracked_object) -> str | None:
        obj = getattr(tracked_object, "object", None)
        return getattr(obj, "id", None)
