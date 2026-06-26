from app.wh.runtime.vision.vision_task_compiler import (
    VisionTaskCompiler
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_vision_task_compiler():

    offer = (

        ConstructionOffer()

    )

    offer.security.rc2 = (

        True

    )

    offer.hardware.hidden_hinges = (

        True

    )

    compiler = (

        VisionTaskCompiler()

    )

    tasks = (

        compiler.compile(

            offer

        )

    )

    assert (

        len(

            tasks

        )

        ==

        2

    )

    assert (

        tasks[0].name

        ==

        "configure_security"

    )

    assert (

        tasks[1].name

        ==

        "configure_hardware"

    )