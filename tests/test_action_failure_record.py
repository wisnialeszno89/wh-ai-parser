from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.action_failure_record import (
    ActionFailureRecord,
)


def test_action_failure_record_stores_failure_data():

    record = ActionFailureRecord(
        action_name="test_action",
        reason="Action failed.",
        attempts=2,
        decision=ActionFailureDecision.SKIP,
    )

    assert (
        record.action_name
        == "test_action"
    )

    assert (
        record.reason
        == "Action failed."
    )

    assert record.attempts == 2

    assert (
        record.decision
        == ActionFailureDecision.SKIP
    )
