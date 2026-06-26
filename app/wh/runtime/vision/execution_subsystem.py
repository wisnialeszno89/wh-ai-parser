from app.wh.runtime.vision.offer_execution_planner import (
    OfferExecutionPlanner
)

from app.wh.runtime.vision.intelligent_vision_executor import (
    IntelligentVisionExecutor
)

from app.wh.runtime.vision.offer_execution_pipeline import (
    OfferExecutionPipeline
)

from app.wh.runtime.vision.execution_verification_pipeline import (
    ExecutionVerificationPipeline
)

from app.wh.runtime.vision.self_healing_execution_pipeline import (
    SelfHealingExecutionPipeline
)

from app.wh.runtime.vision.adaptive_self_healing_pipeline import (
    AdaptiveSelfHealingPipeline
)


class ExecutionSubsystem:

    def __init__(

        self,

        brain

    ):

        self.offer_execution_planner = (

            OfferExecutionPlanner()

        )

        self.intelligent_vision_executor = (

            IntelligentVisionExecutor()

        )

        self.offer_execution_pipeline = (

            OfferExecutionPipeline(

                brain

            )

        )

        self.execution_verification_pipeline = (

            ExecutionVerificationPipeline(

                brain

            )

        )

        self.self_healing_execution_pipeline = (

            SelfHealingExecutionPipeline(

                brain

            )

        )

        self.adaptive_self_healing_pipeline = (

            AdaptiveSelfHealingPipeline(

                brain

            )

        )