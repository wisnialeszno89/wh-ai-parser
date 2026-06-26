from app.wh.runtime.segment_action_planner import (
    SegmentActionPlanner
)

from app.wh.model.opening import (
    Opening
)


def test_segment_action_planner_hst():

    planner = SegmentActionPlanner()

    actions = planner.plan(

        Opening.HST

    )

    assert actions[0].name == "frame"

    assert actions[1].name == "hst_active_leaf"

    assert actions[2].name == "hst_passive_leaf"

    assert actions[3].name == "glass"