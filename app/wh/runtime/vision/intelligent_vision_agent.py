from app.wh.runtime.vision.gui_agent import (
    GUIAgent
)

from app.wh.runtime.vision.execution_logger import (
    ExecutionLogger
)

from app.wh.runtime.vision.retry_engine import (
    RetryEngine
)

from app.wh.runtime.vision.recovery_engine import (
    RecoveryEngine
)

from app.wh.runtime.vision.goal_result_factory import (
    GoalResultFactory
)

from app.wh.runtime.vision.pre_execution_advisor import (
    PreExecutionAdvisor
)

from app.wh.runtime.vision.execution_context_builder import (
    ExecutionContextBuilder
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


class IntelligentVisionAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.runtime = runtime

        self.brain = brain

        self.agent = (

            GUIAgent(

                runtime

            )

        )

        self.logger = (

            ExecutionLogger()

        )

        self.retry_engine = (

            RetryEngine()

        )

        self.recovery_engine = (

            RecoveryEngine()

        )

        self.result_factory = (

            GoalResultFactory()

        )

        self.pre_execution_advisor = (

            PreExecutionAdvisor()

        )

        self.context_builder = (

            ExecutionContextBuilder()

        )

    def execute(

        self,

        goal

    ):

        self.brain.current_goal = (

            goal

        )

        advice = (

            self.pre_execution_advisor.advise(

                goal,

                self.brain

            )

        )

        if (

            advice.strategy

            ==

            PredictionStrategy.REQUIRE_HUMAN_REVIEW

        ):

            return (

                self.result_factory.human_review(

                    advice.risk_reason

                )

            )

        decision = (

            self.brain.vision_reasoning_engine.decide(

                goal,

                self.brain

            )

        )

        if not (

            decision.execute

        ):

            self.logger.log(

                goal,

                decision,

                True,

                self.brain

            )

            return (

                self.result_factory.skipped(

                    decision.reason

                )

            )

        context = (

            self.context_builder.build(

                goal,

                self.brain

            )

        )

        result = (

            self.retry_engine.execute(

                lambda:

                self.agent.execute(

                    goal,

                    context

                ),

                retry_count=context.retry_count

            )

        )

        if not result:

            self.recovery_engine.recover(

                self.brain

            )

            result = (

                self.retry_engine.execute(

                    lambda:

                    self.agent.execute(

                        goal,

                        context

                    ),

                    retry_count=context.retry_count

                )

            )

        if result:

            self.brain.goal_memory.remember(

                goal

            )

            self.logger.log(

                goal,

                decision,

                True,

                self.brain

            )

            return (

                self.result_factory.success()

            )

        self.logger.log(

            goal,

            decision,

            False,

            self.brain

        )

        return (

            self.result_factory.failed(

                "execution_failed"

            )

        )