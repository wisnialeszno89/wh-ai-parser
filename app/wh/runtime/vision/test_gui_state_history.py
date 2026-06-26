from app.wh.runtime.vision.gui_state_history import (
    GUIStateHistory
)

from app.wh.runtime.vision.gui_state_snapshot import (
    GUIStateSnapshot
)


def test_gui_state_history():

    history = (

        GUIStateHistory()

    )

    history.remember(

        GUIStateSnapshot(

            current_tab="security"

        )

    )

    history.remember(

        GUIStateSnapshot(

            current_tab="hardware"

        )

    )

    assert (

        history.count()

        ==

        2

    )

    assert (

        history.last().current_tab

        ==

        "hardware"

    )