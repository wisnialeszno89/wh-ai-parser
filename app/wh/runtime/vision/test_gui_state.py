from app.wh.runtime.vision.gui_state import (
    GUIState
)


def test_gui_state():

    state = (

        GUIState()

    )

    assert (

        state.current_tab

        is None

    )

    assert (

        state.current_dialog

        is None

    )

    state.current_tab = (

        "hardware"

    )

    state.current_dialog = (

        "color"

    )

    assert (

        state.current_tab

        ==

        "hardware"

    )

    assert (

        state.current_dialog

        ==

        "color"

    )