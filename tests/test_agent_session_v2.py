from app.runtime.agent_session import (
    AgentSession
)


def test_agent_session_v2():

    session = AgentSession()

    session.run(

        """

1500x1400 FIX RU FIX

Veka Softline 82

Ug 0.5

antracyt / biały

"""

    )

    assert len(

        session.logs

    ) > 0

    assert len(

        session.logger.entries

    ) == 2