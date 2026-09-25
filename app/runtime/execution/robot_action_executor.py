from dataclasses import dataclass
from enum import Enum

from app.runtime.execution.action_result import ActionResult
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
)
from app.runtime.execution.vision.bridges.tracked_object_gui_bridge import (
    TrackedObjectGUIBridge,
)


class RobotExecutionMode(Enum):
    DRY_RUN = "dry_run"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class RobotActionResult:
    """
    Result of a universal robot action.

    The result deliberately separates:
        - whether the action was accepted,
        - whether hardware was actually touched,
        - the resolved GUI target,
        - the resolved screen point.
    """

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
    First universal execution layer for the desktop robot.

    Pipeline:

        TrackedObject
            -> safety gate
            -> GUIObject bridge
            -> target point
            -> dry-run / live dispatch

    DRY_RUN never touches the mouse.
    """

    def __init__(
        self,
        *,
        mode: RobotExecutionMode = RobotExecutionMode.DRY_RUN,
        safety_gate: ExecutionSafetyGate | None = None,
        bridge: TrackedObjectGUIBridge | None = None,
    ) -> None:
        self.mode = mode
        self.safety_gate = safety_gate or ExecutionSafetyGate()
        self.bridge = bridge or TrackedObjectGUIBridge()

    def execute(
        self,
        *,
        tracked_object,
        action: InteractionAction,
        root,
    ) -> RobotActionResult:
        if not self.safety_gate.can_execute(
            tracked_object,
            action,
        ):
            return RobotActionResult(
                success=False,
                action=action,
                mode=self.mode,
                executed=False,
                target_id=self._target_id(tracked_object),
                confidence=self._confidence(tracked_object),
                reason="Safety gate rejected action",
            )

        target = self.bridge.resolve(
            tracked_object,
            root,
        )

        if target is None:
            return RobotActionResult(
                success=False,
                action=action,
                mode=self.mode,
                executed=False,
                confidence=self._confidence(tracked_object),
                reason="Tracked object could not be resolved to GUIObject",
            )

        point = self._center(target)
        target_id = getattr(target, "id", None)
        confidence = self._confidence(tracked_object)

        if self.mode is RobotExecutionMode.DRY_RUN:
            return RobotActionResult(
                success=True,
                action=action,
                mode=self.mode,
                executed=False,
                target_id=target_id,
                point=point,
                confidence=confidence,
                reason="Dry-run action accepted; hardware not touched",
            )

        return self._execute_live(
            tracked_object=tracked_object,
            target=target,
            action=action,
            point=point,
            confidence=confidence,
        )

    def _execute_live(
        self,
        *,
        tracked_object,
        target,
        action: InteractionAction,
        point: tuple[int, int],
        confidence: float,
    ) -> RobotActionResult:
        """
        LIVE execution is intentionally not implemented yet.

        The first milestone is to prove the complete semantic path
        without touching hardware.
        """
        return RobotActionResult(
            success=False,
            action=action,
            mode=self.mode,
            executed=False,
            target_id=getattr(target, "id", None),
            point=point,
            confidence=confidence,
            reason="LIVE execution is not enabled in Hands v1",
        )

    @staticmethod
    def _center(target) -> tuple[int, int]:
        bounds = target.bounds
        if bounds is None:
            raise ValueError(
                "Resolved GUIObject has no bounds"
            )

        return (
            bounds.x + bounds.width // 2,
            bounds.y + bounds.height // 2,
        )

    @staticmethod
    def _confidence(tracked_object) -> float:
        return float(
            getattr(tracked_object, "confidence", 0.0)
        )

    @staticmethod
    def _target_id(tracked_object) -> str | None:
        obj = getattr(tracked_object, "object", None)
        return getattr(obj, "id", None)
