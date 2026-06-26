from app.wh.runtime.vision.cognitive_loop_report import (
    CognitiveLoopReport
)


class CognitiveLoopEngine:

    def run(

        self,

        brain

    ):

        optimization_report = (

            brain.self_optimization_engine.analyze(

                brain

            )

        )

        return (

            CognitiveLoopReport(

                confidence_level=(

                    optimization_report.confidence_level

                ),

                recovery_patterns=(

                    optimization_report.total_recovery_patterns

                ),

                meta_patterns=(

                    optimization_report.total_meta_patterns

                )

            )

        )