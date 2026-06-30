from app.agent.agent_phase import (
    AgentPhase
)


class AgentCycle:

    def __init__(self):

        self.phase = (
            AgentPhase.READ_CONTEXT
        )

    def next(self):

        order = [

            AgentPhase.READ_CONTEXT,

            AgentPhase.PLAN,

            AgentPhase.BUILD_CONSTRUCTION,

            AgentPhase.BUILD_GUI,

            AgentPhase.EXECUTE,

            AgentPhase.VERIFY,

            AgentPhase.NEXT_POSITION,

            AgentPhase.FINISHED
        ]

        index = order.index(
            self.phase
        )

        if index < len(order) - 1:

            self.phase = order[
                index + 1
            ]

        return self.phase