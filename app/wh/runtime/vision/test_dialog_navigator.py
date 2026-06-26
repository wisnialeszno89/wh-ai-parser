from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.dialog_navigator import (
    DialogNavigator
)


def test_dialog_navigator():

    runtime = (

        VisionRuntime()

    )

    navigator = (

        DialogNavigator(

            runtime

        )

    )

    assert (

        navigator.open(

            "color"

        )

        is True

    )

    assert (

        navigator.context.current_dialog

        ==

        "color"

    )

    assert (

        navigator.close()

        is True

    )

    assert (

        navigator.context.current_dialog

        is None

    )