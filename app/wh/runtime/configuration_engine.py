from app.wh.runtime.configuration_report import (
    ConfigurationReport
)

from app.wh.runtime.profile_reasoning_engine import (
    ProfileReasoningEngine
)

from app.wh.runtime.profile_suggestion_engine import (
    ProfileSuggestionEngine
)

from app.wh.runtime.profile_optimizer import (
    ProfileOptimizer
)


class ConfigurationEngine:

    def __init__(

        self

    ):

        self.reasoning_engine = (

            ProfileReasoningEngine()

        )

        self.suggestion_engine = (

            ProfileSuggestionEngine()

        )

        self.optimizer = (

            ProfileOptimizer()

        )

    def analyze(

        self,

        offer

    ):

        report = (

            ConfigurationReport()

        )

        report.problems = (

            self.reasoning_engine.validate(

                offer

            )

        )

        report.suggestions = (

            self.suggestion_engine.suggest(

                offer

            )

        )

        report.optimized_offer = (

            self.optimizer.optimize(

                offer

            )

        )

        return report