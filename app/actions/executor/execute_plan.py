from app.actions.executor.execute_action import (
    execute_action
)


def execute_plan(

    plan,

    ui_graph
):

    for action in plan.actions:

        execute_action(

            action,

            ui_graph
        )