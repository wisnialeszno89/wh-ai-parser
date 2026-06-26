from app.wh.runtime.vision.gui_brain import (
    GUIBrain
)


def test_gui_brain():

    brain = (

        GUIBrain()

    )

    brain.state.current_tab = (

        "hardware"

    )

    assert (

        brain.state.current_tab

        ==

        "hardware"

    )