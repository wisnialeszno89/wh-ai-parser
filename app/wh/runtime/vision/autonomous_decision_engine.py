from app.wh.runtime.vision.autonomous_decision import (
    AutonomousDecision
)


class AutonomousDecisionEngine:

    def decide(

        self,

        confidence,

        brain

    ):

        confidence_decision = (

            brain.confidence_engine.evaluate(

                confidence

            )

        )

        mode_decision = (

            brain.confidence_adaptive_mode_engine.decide(

                confidence_decision

            )

        )

        return (

            AutonomousDecision(

                mode=mode_decision.mode,

                confidence_level=confidence_decision.level,

                confidence=confidence

            )

        )