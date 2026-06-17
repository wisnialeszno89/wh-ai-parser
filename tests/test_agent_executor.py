from app.knowledge.gui.gui_action import (
    GUIAction
)

from app.runtime.agent_executor import (
    AgentExecutor
)


def test_agent_executor():

    actions = [

        GUIAction(

            action="select",

            screen="offer",

            control="profile",

            value="Veka Softline 82"

        )

    ]

    executor = AgentExecutor()

    commands = executor.execute(

        actions

    )

    assert len(

        commands

    ) > 0