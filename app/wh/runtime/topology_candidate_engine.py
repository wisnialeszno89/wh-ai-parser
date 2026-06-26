from app.wh.runtime.topology_candidate import (
    TopologyCandidate
)


class TopologyCandidateEngine:

    def generate(

        self,

        project

    ):

        width = (

            project.schema.width

        )

        candidates = []

        if width <= 2500:

            candidates.append(

                TopologyCandidate(

                    notation="RU"

                )

            )

        elif width <= 4000:

            candidates.extend(

                [

                    TopologyCandidate(

                        notation="RU|FIX"

                    ),

                    TopologyCandidate(

                        notation="FIX|RU"

                    )

                ]

            )

        else:

            candidates.extend(

                [

                    TopologyCandidate(

                        notation="RU|FIX|RU"

                    ),

                    TopologyCandidate(

                        notation="FIX|RU|FIX"

                    )

                ]

            )

        return candidates