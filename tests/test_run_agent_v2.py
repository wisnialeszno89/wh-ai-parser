from app.runtime.run_agent import (
    run_agent
)


def test_run_agent_v2():

    commands = run_agent(

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