from __future__ import annotations

from ctypes import Structure, Union, byref, c_long, c_ulong, c_void_p, sizeof, windll
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


class _MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouse_data", c_ulong),
        ("flags", c_ulong),
        ("time", c_ulong),
        ("extra_info", c_void_p),
    ]


class _INPUT_UNION(Union):
    _fields_ = [
        ("mouse", _MOUSEINPUT),
    ]


class _INPUT(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("union", _INPUT_UNION),
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
        inputs[0].union.mouse.flags = self._MOUSEEVENTF_LEFTDOWN
        inputs[1].union.mouse.flags = self._MOUSEEVENTF_LEFTUP

        sent = windll.user32.SendInput(
            2,
            byref(inputs),
            sizeof(_INPUT),
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
