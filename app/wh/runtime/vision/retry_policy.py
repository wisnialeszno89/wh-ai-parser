from app.wh.runtime.vision.wait_agent import (
    WaitAgent
)


class RetryPolicy:

    def __init__(

        self

    ):

        self.wait_agent = (

            WaitAgent()

        )

    def execute(

        self,

        callback,

        attempts=3,

        delay=0

    ):

        for attempt in range(

            attempts

        ):

            result = (

                callback()

            )

            if result:

                return True

            if attempt < attempts - 1:

                self.wait_agent.wait(

                    delay

                )

        return False