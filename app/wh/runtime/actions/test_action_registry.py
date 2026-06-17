from app.wh.runtime.actions.action_registry import (
    ActionRegistry
)


def test_action_registry():

    registry = ActionRegistry()

    frame = registry.get(

        "frame"

    )

    assert frame.name == "frame"

    assert (

        frame.template_path

        ==

        "tests/data/frame_button.png"

    )