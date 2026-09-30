from dataclasses import dataclass
from enum import Enum

from app.runtime.execution.action_policy import ActionPolicy
from app.runtime.execution.action_result import ActionResult
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
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

        if action is not InteractionAction.CLICK:
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
