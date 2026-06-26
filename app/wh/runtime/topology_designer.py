from app.wh.runtime.topology_candidate_engine import (
    TopologyCandidateEngine
)

from app.wh.runtime.topology_scoring_engine import (
    TopologyScoringEngine
)


class TopologyDesigner:

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

        return max(

            scored,

            key=lambda x: x.score

        )