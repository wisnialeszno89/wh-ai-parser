import app.runtime.execution.robot_mouse as robot_mouse_module
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode


def test_robot_mouse_dry_run_never_touches_hardware():
    mouse = RobotMouse(mode=RobotMouseMode.DRY_RUN)

    result = mouse.click(321, 654)

    assert result.success is True
    assert result.executed is False
    assert result.mode is RobotMouseMode.DRY_RUN
    assert result.point == (321, 654)
    assert "hardware not touched" in result.reason


def test_robot_mouse_live_uses_windows_api_without_physical_click(
    monkeypatch,
):
    calls = []

    class FakeUser32:
        def SetCursorPos(self, x, y):
            calls.append(("SetCursorPos", x, y))
            return 1

        def SendInput(self, count, inputs, input_size):
            calls.append(
                ("SendInput", count, input_size)
            )
            return count

    class FakeWindll:
        user32 = FakeUser32()

    monkeypatch.setattr(
        robot_mouse_module,
        "windll",
        FakeWindll(),
    )

    mouse = RobotMouse(mode=RobotMouseMode.LIVE)

    result = mouse.click(321, 654)

    assert result.success is True
    assert result.executed is True
    assert result.mode is RobotMouseMode.LIVE
    assert result.point == (321, 654)
    assert "Windows SendInput" in result.reason
    assert calls[0] == (
        "SetCursorPos",
        321,
        654,
    )
    assert calls[1][0] == "SendInput"
    assert calls[1][1] == 2
    assert calls[1][2] > 0
