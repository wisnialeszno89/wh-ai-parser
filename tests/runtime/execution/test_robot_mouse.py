from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode


def test_robot_mouse_dry_run_never_touches_hardware():
    mouse = RobotMouse(mode=RobotMouseMode.DRY_RUN)

    result = mouse.click(123, 456)

    assert result.success is True
    assert result.executed is False
    assert result.mode is RobotMouseMode.DRY_RUN
    assert result.point == (123, 456)
    assert "hardware not touched" in result.reason


def test_robot_mouse_live_is_locked():
    mouse = RobotMouse(mode=RobotMouseMode.LIVE)

    result = mouse.click(123, 456)

    assert result.success is False
    assert result.executed is False
    assert result.mode is RobotMouseMode.LIVE
    assert result.point == (123, 456)
    assert "locked" in result.reason
