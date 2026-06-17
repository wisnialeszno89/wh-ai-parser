from app.runtime.agent_logger import (
    AgentLogger
)


def test_agent_logger():

    logger = AgentLogger()

    logger.log(

        "START SESSION"

    )

    logger.log(

        "END SESSION"

    )

    assert len(

        logger.entries

    ) == 2