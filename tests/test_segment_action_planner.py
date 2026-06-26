from app.wh.runtime.segment_action_planner import (
    SegmentActionPlanner
)

from app.wh.model.opening import (
    Opening
)


def test_segment_action_planner():

    planner = SegmentActionPlanner()

    actions = planner.plan(

        Opening.TILT_TURN

    )

    assert actions[0].name == "frame"

    assert actions[1].name == "sash"

    assert actions[2].name == "glass"

    actions = planner.plan(

        Opening.FIX

    )

    assert actions[0].name == "frame"

    assert actions[1].name == "glass"