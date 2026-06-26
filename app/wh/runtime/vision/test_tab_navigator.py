from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.tab_navigator import (
    TabNavigator
)


def test_tab_navigator():

    runtime = (

        VisionRuntime()

    )

    navigator = (

        TabNavigator(

            runtime

        )

    )

    assert (

        navigator.goto(

            "hardware"

        )

        is True

    )

    assert (

        navigator.context.current_tab

        ==

        "hardware"

    )

    assert (

        navigator.goto(

            "glass"

        )

        is True

    )

    assert (

        navigator.context.current_tab

        ==

        "glass"

    )