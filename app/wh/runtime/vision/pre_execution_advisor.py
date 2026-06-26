from app.wh.runtime.vision.pre_execution_advice import (
    PreExecutionAdvice
)


class PreExecutionAdvisor:

    def advise(

        self,

        goal,

        brain

    ):

        warning = (

            brain.predictive_reasoning_engine.predict(

                goal,

                brain

            )

        )

        decision = (

            brain.predictive_decision_engine.decide(

                warning

            )

        )

        strategy = (

            brain.predictive_strategy_engine.decide(

                decision

            )

        )

        return (

            PreExecutionAdvice(

                strategy=strategy,

                risk_reason=decision.reason,

                confidence=decision.confidence

            )

        )