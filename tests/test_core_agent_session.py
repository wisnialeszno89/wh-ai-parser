from app.agent.core.agent_session import (
    AgentSession,
)


def test_agent_session_has_default_state():

    session = AgentSession(
        session_id="session-1"
    )

    assert session.session_id == "session-1"
    assert session.salesman_id is None
    assert session.history == []
    assert session.state is not None
    assert session.state.offer_session is not None


def test_agent_session_remembers_messages():

    session = AgentSession(
        session_id="session-1"
    )

    session.remember("Pierwsza wiadomość")
    session.remember("Druga wiadomość")

    assert session.history == [
        "Pierwsza wiadomość",
        "Druga wiadomość",
    ]


def test_agent_session_keeps_offer_session_inside_state():

    session = AgentSession(
        session_id="session-1"
    )

    offer_session = session.state.offer_session

    assert offer_session.current_context is None
    assert offer_session.workflow_state.value == "new"
