from unittest.mock import (
    MagicMock
)

from app.wh.runtime.agent.window_agent import (
    WindowAgent
)


def test_window_agent():

    agent = WindowAgent()

    agent.construction_executor = (

        MagicMock()

    )

    text = """

    okno 2000 na 1500

    r+f

    sl82

    pakiet trzyszybowy

    """

    result = agent.execute(

        text

    )

    agent.construction_executor.execute.assert_called_once()

    assert result is True