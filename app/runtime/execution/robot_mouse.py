from __future__ import annotations

from ctypes import POINTER, Structure, byref, c_int, c_uint, c_ulong, windll
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


class _INPUT(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("_padding", c_ulong * 7),
    ]


class RobotMouse:
    """
    Hardware adapter for the universal robot.

    DRY_RUN computes the click target without touching hardware.
    LIVE uses the native Windows SendInput API.
    """

    _INPUT_MOUSE = 0
    _MOUSEEVENTF_LEFTDOWN = 0x0002
    _MOUSEEVENTF_LEFTUP = 0x0004

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

        if windll.user32.SetCursorPos(*point) == 0:
            return RobotMouseResult(
                success=False,
                executed=False,
                mode=self.mode,
                point=point,
                reason="Windows SetCursorPos failed",
            )

        inputs = (_INPUT * 2)()
        inputs[0].type = self._INPUT_MOUSE
        inputs[1].type = self._INPUT_MOUSE

        # SendInput accepts MOUSEINPUT through the same native INPUT layout.
        # The union is padded above so dwFlags lands at the expected offset
        # for the 64-bit Windows ABI used by the supported runtime.
        inputs[0]._padding[2] = self._MOUSEEVENTF_LEFTDOWN
        inputs[1]._padding[2] = self._MOUSEEVENTF_LEFTUP

        sent = windll.user32.SendInput(
            2,
            byref(inputs),
            0x28,
        )

        if sent != 2:
            return RobotMouseResult(
                success=False,
                executed=False,
                mode=self.mode,
                point=point,
                reason=f"Windows SendInput failed after cursor move (sent={sent})",
            )

        return RobotMouseResult(
            success=True,
            executed=True,
            mode=self.mode,
            point=point,
            reason="LIVE mouse click executed via Windows SendInput",
        )
