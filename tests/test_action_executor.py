from app.wh.runtime.action_executor import (
    ActionExecutor
)


def test_action_executor():

    executor = ActionExecutor()

    assert executor is not None