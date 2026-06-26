from app.wh.runtime.segment_action_planner import (
    SegmentActionPlanner
)

from app.wh.model.opening import (
    Opening
)


def test_segment_action_planner_psk():

    planner = SegmentActionPlanner()

    actions = planner.plan(

        Opening.PSK

    )

    assert actions[0].name == "frame"

    assert actions[1].name == "psk_sash"

    assert actions[2].name == "glass"