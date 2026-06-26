from app.wh.runtime.vision.vision_action_factory import (
    VisionActionFactory
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_vision_action_factory():

    factory = (

        VisionActionFactory()

    )

    action = (

        factory.create(

            GUIGoal(

                "enable_rc2"

            )

        )

    )

    assert (

        action.name

        ==

        "enable_rc2"

    )

    assert (

        action.template_path

        ==

        "templates/enable_rc2.png"

    )