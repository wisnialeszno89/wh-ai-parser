from app.wh.runtime.design_report import (
    DesignReport
)

from app.wh.runtime.topology_candidate_engine import (
    TopologyCandidateEngine
)

from app.wh.runtime.topology_scoring_engine import (
    TopologyScoringEngine
)


class DesignEngine:

    def __init__(

        self

    ):

        self.candidate_engine = (

            TopologyCandidateEngine()

        )

        self.scoring_engine = (

            TopologyScoringEngine()

        )

    def design(

        self,

        project

    ):

        report = (

            DesignReport()

        )

        candidates = (

            self.candidate_engine.generate(

                project

            )

        )

        scored = []

        for candidate in candidates:

            scored.append(

                self.scoring_engine.score(

                    candidate,

                    project

                )

            )

        report.candidates = (

            sorted(

                scored,

                key=lambda x: x.score,

                reverse=True

            )

        )

        report.winner = (

            report.candidates[0]

        )

        return report