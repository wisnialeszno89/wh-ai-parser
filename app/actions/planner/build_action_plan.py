from app.actions.models.action import (
    Action
)

from app.actions.models.action_plan import (
    ActionPlan
)


def build_action_plan(

    construction_graph,

    ui_graph
):

    plan = ActionPlan()

    plan.actions.append(

        Action(

            action_type="select_tool",

            tool_name="frame_tool"
        )
    )

    plan.actions.append(

        Action(

            action_type="draw_frame"
        )
    )

    segments = [

        obj

        for obj in construction_graph.objects

        if obj.object_type == "segment"
    ]

    if len(segments) > 1:

        plan.actions.append(

            Action(

                action_type="select_tool",

                tool_name="mullion_tool"
            )
        )

        plan.actions.append(

            Action(

                action_type="insert_mullion"
            )
        )

    return plan