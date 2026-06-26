from app.wh.runtime.vision.gui_state_snapshot import (
    GUIStateSnapshot
)


def test_gui_state_snapshot():

    snapshot = (

        GUIStateSnapshot(

            current_tab="hardware",

            selected_color="winchester"

        )

    )

    assert (

        snapshot.current_tab

        ==

        "hardware"

    )

    assert (

        snapshot.selected_color

        ==

        "winchester"

    )

    assert (

        snapshot.selected_profile

        is None

    )