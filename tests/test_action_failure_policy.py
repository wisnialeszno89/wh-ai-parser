from app.agent.agent_action import (
    AgentAction,
)

from app.agent.agent_request import (
    AgentRequest,
)

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.default_action_failure_policy import (
    DefaultActionFailurePolicy,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


def create_action():

    return AgentAction(
        name="test_action",
        description="Test action",
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Execute action.",
        )
    )


def test_default_policy_stops_on_failure():

    policy = (
        DefaultActionFailurePolicy()
    )

    result = ExecutionLoopResult(
        attempts=(),
        success=False,
    )

    decision = policy.decide(
        create_action(),
        result,
        create_context(),
    )

    assert (
        decision
        == ActionFailureDecision.STOP
    )


def test_default_policy_requests_manual_review():

    policy = (
        DefaultActionFailurePolicy()
    )

    result = ExecutionLoopResult(
        attempts=(),
        success=False,
        requires_manual_review=True,
    )

    decision = policy.decide(
        create_action(),
        result,
        create_context(),
    )

    assert (
        decision
        == ActionFailureDecision.MANUAL_REVIEW
    )


def test_default_policy_stops_when_execution_stopped():

    policy = (
        DefaultActionFailurePolicy()
    )

    result = ExecutionLoopResult(
        attempts=(),
        success=False,
        stopped=True,
    )

    decision = policy.decide(
        create_action(),
        result,
        create_context(),
    )

    assert (
        decision
        == ActionFailureDecision.STOP
    )
