from app.wh.companion.companion_client import (
    CompanionClient
)


def test_companion_client():

    client = CompanionClient()

    result = client.send(

        {

            "action":

            "ping"

        }

    )

    assert result["success"]