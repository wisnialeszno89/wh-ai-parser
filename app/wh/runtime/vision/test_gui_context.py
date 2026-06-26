from app.wh.runtime.vision.gui_context import (
    GUIContext
)


def test_gui_context():

    context = (

        GUIContext()

    )

    assert (

        context.current_tab

        is None

    )

    context.current_tab = (

        "hardware"

    )

    assert (

        context.current_tab

        ==

        "hardware"

    )

    context.current_dialog = (

        "color_dialog"

    )

    assert (

        context.current_dialog

        ==

        "color_dialog"

    )