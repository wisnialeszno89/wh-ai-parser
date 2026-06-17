from app.wh.runtime.field_action_planner import (
    FieldActionPlanner
)


def test_field_action_planner():

    planner = FieldActionPlanner()

    fields = [

        {

            "id":1,

            "type":"active"

        },

        {

            "id":2,

            "type":"fixed"

        }

    ]

    result = planner.plan(

        fields

    )

    assert result[0]["actions"] == [

        "frame",

        "sash",

        "glass"

    ]

    assert result[1]["actions"] == [

        "frame",

        "glass"

    ]