from app.wh.runtime.vision.failure_decision import (
    FailureDecision
)


class FailureReasoningEngine:

    def decide(

        self,

        reason,

        brain

    ):

        action = (

            brain.failure_strategy_engine.decide(

                reason

            )

        )

        return (

            FailureDecision(

                action=action,

                reason=reason

            )

        )