from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RobotMouseMode(Enum):
    DRY_RUN = "dry_run"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class RobotMouseResult:
    success: bool
    executed: bool
    mode: RobotMouseMode
    point: tuple[int, int]
    reason: str


class RobotMouse:
    """
    Hardware adapter for the universal robot.

    DRY_RUN is the only executable mode in v1.
    LIVE is intentionally locked until the complete execution
    safety chain is ready.
    """

    def __init__(self, *, mode: RobotMouseMode = RobotMouseMode.DRY_RUN):
        self.mode = mode

    def click(self, x: int, y: int) -> RobotMouseResult:
        point = (int(x), int(y))

        if self.mode is RobotMouseMode.DRY_RUN:
            return RobotMouseResult(
                success=True,
                executed=False,
                mode=self.mode,
                point=point,
                reason="Dry-run mouse click accepted; hardware not touched",
            )

        return RobotMouseResult(
            success=False,
            executed=False,
            mode=self.mode,
            point=point,
            reason="LIVE mouse execution is locked in RobotMouse v1",
        )
