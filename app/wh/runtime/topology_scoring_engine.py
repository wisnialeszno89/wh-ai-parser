class TopologyScoringEngine:

    def score(

        self,

        candidate,

        project

    ):

        score = 0.0

        notation = (

            candidate.notation

        )

        if notation == (

            "RU"

        ):

            score = 1.0

        elif notation in (

            "RU|FIX",

            "FIX|RU"

        ):

            score = 0.9

        elif notation == (

            "RU|FIX|RU"

        ):

            score = 0.95

        elif notation == (

            "FIX|RU|FIX"

        ):

            score = 0.8

        candidate.score = (

            score

        )

        return candidate