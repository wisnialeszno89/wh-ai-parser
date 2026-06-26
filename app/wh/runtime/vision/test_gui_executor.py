from app.wh.runtime.vision.gui_executor import (
    GUIExecutor
)

from app.wh.runtime.vision.gui_plan import (
    GUIPlan
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)


def test_gui_executor():

    runtime = (

        VisionRuntime()

    )

    executor = (

        GUIExecutor(

            runtime

        )

    )

    plan = (

        GUIPlan()

    )

    plan.add(

        "goto_hardware"

    )

    plan.add(

        "enable_rc2"

    )

    assert (

        executor.execute(

            plan

        )

        is True

    )