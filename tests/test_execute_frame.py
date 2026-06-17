from app.wh.runtime.action_executor import (
    ActionExecutor
)


def test_execute_frame():

    executor = ActionExecutor()

    result = executor.execute_action(

        "frame"

    )

    print()

    print(result)

    assert result.confidence > 0.8