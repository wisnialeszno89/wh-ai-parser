from app.runtime.run_agent import (
    run_agent
)

from app.runtime.agent_logger import (
    AgentLogger
)

from app.runtime.agent_memory import (
    AgentMemory
)

from app.runtime.agent_state import (
    AgentState
)

from app.runtime.agent_error_handler import (
    AgentErrorHandler
)


class AgentSession:

    def __init__(
        self
    ):

        self.logs = []

        self.logger = AgentLogger()

        self.memory = AgentMemory()

        self.state = AgentState.IDLE

        self.error_handler = AgentErrorHandler()

    def run(
        self,
        customer_text
    ):

        try:

            self.state = AgentState.RUNNING

            self.logger.log(

                "START SESSION"

            )

            self.memory.last_customer = (

                customer_text

            )

            commands = run_agent(

                customer_text

            )

            self.logs.extend(

                commands

            )

            self.logger.log(

                "END SESSION"

            )

            self.state = AgentState.FINISHED

            return commands

        except Exception as e:

            self.state = AgentState.ERROR

            self.logger.log(

                self.error_handler.handle(

                    e

                )

            )

            raise