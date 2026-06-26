from app.wh.runtime.topology_suggestion import (
    TopologySuggestion
)


class TopologyOptimizer:

    def suggest(

        self,

        project

    ):

        width = (

            project.schema.width

        )

        height = (

            project.schema.height

        )

        suggestions = []

        if width <= 2500:

            suggestions.append(

                TopologySuggestion(

                    notation="RU",

                    reason="Jednoskrzydłowe"

                )

            )

        elif width <= 4000:

            suggestions.append(

                TopologySuggestion(

                    notation="RU|FIX",

                    reason="Dwupolowe"

                )

            )

        else:

            suggestions.append(

                TopologySuggestion(

                    notation="RU|FIX|RU",

                    reason="Szeroka konstrukcja"

                )

            )

        return suggestions