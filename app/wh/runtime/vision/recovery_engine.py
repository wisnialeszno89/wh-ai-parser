from app.wh.runtime.vision.recovery_strategy import (
    RecoveryStrategy
)


class RecoveryEngine:

    def __init__(

        self

    ):

        self.strategy = (

            RecoveryStrategy()

        )

    def recover(

        self,

        brain

    ):

        return (

            self.strategy.recover(

                brain

            )

        )