from app.wh.runtime.vision.recovery_knowledge_base import (
    RecoveryKnowledgeBase
)

from app.wh.runtime.vision.recovery_strategy_selector import (
    RecoveryStrategySelector
)

from app.wh.runtime.vision.adaptive_recovery_engine import (
    AdaptiveRecoveryEngine
)

from app.wh.runtime.vision.adaptive_self_healing_pipeline import (
    AdaptiveSelfHealingPipeline
)


class RecoverySubsystem:

    def __init__(

        self,

        brain

    ):

        self.recovery_knowledge_base = (

            RecoveryKnowledgeBase()

        )

        self.recovery_strategy_selector = (

            RecoveryStrategySelector()

        )

        self.adaptive_recovery_engine = (

            AdaptiveRecoveryEngine()

        )

        self.adaptive_self_healing_pipeline = (

            AdaptiveSelfHealingPipeline(

                brain

            )

        )