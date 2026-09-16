from app.runtime.agent_session import (
    AgentSession
)


def test_agent_session():

    session = AgentSession()

    commands = session.run(

        """

1500x1400 FIX RU FIX

Veka Softline 82

Ug 0.5

antracyt / biały

"""

    )

    assert len(

        commands

    ) > 0

    assert len(

        session.logs

    ) > 0

def test_agent_session_has_offer_session():

    session = AgentSession(
        session_id="session-1"
    )

    assert session.state.offer_session is not None
    assert (
        session.state.offer_session.current_context
        is None
    )
