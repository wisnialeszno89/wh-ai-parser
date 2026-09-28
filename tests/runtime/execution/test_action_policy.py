from app.runtime.execution.action_policy import ActionPolicy
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)


def test_action_policy_allows_click_by_default():
    policy = ActionPolicy()

    assert policy.can_execute(InteractionAction.CLICK) is True


def test_action_policy_rejects_other_actions_by_default():
    policy = ActionPolicy()

    assert policy.can_execute(InteractionAction.DOUBLE_CLICK) is False
    assert policy.can_execute(InteractionAction.RIGHT_CLICK) is False
    assert policy.can_execute(InteractionAction.WRITE) is False
    assert policy.can_execute(InteractionAction.SELECT) is False
    assert policy.can_execute(InteractionAction.WAIT) is False
    assert policy.can_execute(InteractionAction.VERIFY) is False


def test_action_policy_can_be_restricted():
    policy = ActionPolicy(
        allowed_actions=frozenset(),
    )

    assert policy.can_execute(InteractionAction.CLICK) is False


def test_action_policy_can_explicitly_allow_actions():
    policy = ActionPolicy(
        allowed_actions=frozenset(
            {
                InteractionAction.CLICK,
                InteractionAction.WAIT,
            }
        ),
    )

    assert policy.can_execute(InteractionAction.CLICK) is True
    assert policy.can_execute(InteractionAction.WAIT) is True
    assert policy.can_execute(InteractionAction.WRITE) is False
