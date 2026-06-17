from app.runtime.agent_context import (
    AgentContext
)

from app.runtime.agent_state import (
    AgentState
)


def test_agent_context():

    context = AgentContext()

    assert (

        context.state

        ==

        AgentState.IDLE

    )

    assert (

        context.retry_policy.max_retries

        ==

        3

    )

    assert (

        context.metrics.sessions

        ==

        0

    )