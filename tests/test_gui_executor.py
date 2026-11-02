from unittest.mock import MagicMock, patch

from app.wh.runtime.gui_action import GUIAction
from app.wh.runtime.gui_plan import GUIPlan
from app.wh.runtime.gui_executor import GUIExecutor


def test_gui_executor():
    brain = MagicMock()
    brain.execute.side_effect = [
        (100, 200),
        (300, 400),
    ]

    # GUIExecutor orchestration is the unit under test. Do not instantiate
    # the legacy VisionBrain dependency in this test.
    with patch(
        "app.wh.runtime.gui_executor.GUIBrain",
        return_value=brain,
    ):
        executor = GUIExecutor()

    plan = GUIPlan(
        actions=[
            GUIAction(name="add_glass"),
            GUIAction(name="open_properties"),
        ]
    )

    result = executor.execute(
        "screen.png",
        "templates",
        plan,
    )

    assert result == [
        (100, 200),
        (300, 400),
    ]
    assert brain.execute.call_count == 2

    first_command = brain.execute.call_args_list[0].args[2]
    second_command = brain.execute.call_args_list[1].args[2]

    assert first_command.target == "glass_tool.png"
    assert second_command.target == "properties_tool.png"
