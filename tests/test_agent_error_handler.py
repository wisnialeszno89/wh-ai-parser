from app.runtime.agent_error_handler import (
    AgentErrorHandler
)


def test_agent_error_handler():

    handler = AgentErrorHandler()

    result = handler.handle(

        Exception(

            "profile not found"

        )

    )

    assert (

        result

        ==

        "profile not found"

    )