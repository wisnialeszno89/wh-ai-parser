from app.wh.vision.batch_match_analyzer import (
    BatchMatchAnalyzer
)

from app.wh.vision.match_statistics import (
    MatchStatistics
)


class VisionExperience:

    def __init__(

        self

    ):

        self.analyzer = (

            BatchMatchAnalyzer()

        )

        self.statistics = (

            MatchStatistics()

        )

    def learn(

        self,

        screens_dir,

        template_path

    ):

        reports = (

            self.analyzer.analyze(

                screens_dir,

                template_path

            )

        )

        return (

            self.statistics.summarize(

                reports

            )

        )