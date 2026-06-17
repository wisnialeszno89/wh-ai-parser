from app.wh.runtime.action_executor import (
    ActionExecutor
)


def test_execute_sash():

    executor = ActionExecutor()

    result = executor.execute_action(

        "sash"

    )

    print()

    print(result)

    assert result.confidence > 0.8