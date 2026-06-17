from app.runtime.agent_session import (
    AgentSession
)

from app.runtime.agent_state import (
    AgentState
)


def test_agent_session_v4():

    session = AgentSession()

    session.run(

        """

1500x1400 FIX RU FIX

Veka Softline 82

Ug 0.5

antracyt / biały

"""

    )

    assert (

        session.state

        ==

        AgentState.FINISHED

    )