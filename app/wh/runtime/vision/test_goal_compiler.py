from app.wh.runtime.vision.goal_compiler import (
    GoalCompiler
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_goal_compiler():

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

        GoalCompiler()

    )

    goals = (

        compiler.compile(

            offer

        )

    )

    assert (

        len(

            goals

        )

        ==

        2

    )

    assert (

        goals[0]

        .name

        ==

        "enable_rc2"

    )

    assert (

        goals[1]

        .name

        ==

        "enable_hidden_hinges"

    )