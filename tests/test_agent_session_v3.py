from app.runtime.agent_session import (
    AgentSession
)


def test_agent_session_v3():

    text = """

1500x1400 FIX RU FIX

Veka Softline 82

Ug 0.5

antracyt / biały

"""

    session = AgentSession()

    session.run(

        text

    )

    assert (

        session.memory.last_customer

        ==

        text

    )