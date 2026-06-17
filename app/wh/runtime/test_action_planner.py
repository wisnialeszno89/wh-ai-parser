from types import SimpleNamespace

from app.wh.runtime.action_planner import (
    ActionPlanner
)


def test_action_planner():

    planner = (

        ActionPlanner()

    )

    construction = (

        SimpleNamespace(

            segments=[

                SimpleNamespace(

                    kind="frame"

                ),

                SimpleNamespace(

                    kind="sash"

                )

            ]

        )

    )

    actions = (

        planner.plan(

            construction

        )

    )

    assert len(

        actions

    ) == 2

    assert actions[0].name == "frame"

    assert actions[1].name == "sash"