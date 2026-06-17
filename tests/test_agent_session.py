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