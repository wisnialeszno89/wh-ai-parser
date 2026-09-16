from app.agent.session.agent_session_store import (
    AgentSessionStore,
)


def test_store_creates_and_gets_session():

    store = AgentSessionStore()

    session = store.create(
        session_id="session-1",
        salesman_id="salesman-1",
    )

    assert session.session_id == "session-1"
    assert session.salesman_id == "salesman-1"
    assert store.get("session-1") is session


def test_store_get_or_create_reuses_existing_session():

    store = AgentSessionStore()

    first = store.get_or_create(
        session_id="session-1",
        salesman_id="salesman-1",
    )

    first.remember("Pierwsza wiadomość")

    second = store.get_or_create(
        session_id="session-1",
        salesman_id="salesman-1",
    )

    assert second is first
    assert second.history == [
        "Pierwsza wiadomość"
    ]


def test_store_keeps_sessions_isolated():

    store = AgentSessionStore()

    first = store.create(
        session_id="session-1",
        salesman_id="salesman-1",
    )

    second = store.create(
        session_id="session-2",
        salesman_id="salesman-2",
    )

    first.remember("Oferta A")
    second.remember("Oferta B")

    assert first.history == ["Oferta A"]
    assert second.history == ["Oferta B"]
    assert first is not second


def test_store_returns_none_for_unknown_session():

    store = AgentSessionStore()

    assert store.get("unknown") is None


def test_store_save_replaces_session_reference():

    store = AgentSessionStore()

    session = store.create(
        session_id="session-1",
    )

    session.remember("test")

    store.save(session)

    assert store.get("session-1") is session
    assert store.get("session-1").history == ["test"]
