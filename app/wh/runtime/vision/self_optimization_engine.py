from app.wh.runtime.vision.self_optimization_report import (
    SelfOptimizationReport
)


class SelfOptimizationEngine:

    def analyze(

        self,

        brain

    ):

        global_best = (

            brain.global_best_strategy_finder.find(

                brain

            )

        )

        confidence = 0

        if global_best is not None:

            confidence = (

                global_best.confidence

            )

        confidence_decision = (

            brain.confidence_engine.evaluate(

                confidence

            )

        )

        return (

            SelfOptimizationReport(

                confidence_level=(

                    confidence_decision.level

                ),

                total_recovery_patterns=(

                    brain.recovery_learning_memory.count()

                ),

                total_meta_patterns=(

                    brain.meta_learning_memory.count()

                )

            )

        )