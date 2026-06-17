from app.knowledge.executor.execution_result import (
    ExecutionResult
)


def execute(
    gui_actions
):

    executed = []

    for action in gui_actions:

        executed.append(

            (

                action.action,

                action.screen,

                action.control,

                action.value

            )

        )

    return ExecutionResult(

        success=True,

        log=executed

    )