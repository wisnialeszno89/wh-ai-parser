from app.wh.runtime.configuration_suggestion import (
    ConfigurationSuggestion
)

from app.wh.runtime.geometry_knowledge_engine import (
    GeometryKnowledgeEngine
)


class GeometrySuggestionEngine:

    def __init__(

        self

    ):

        self.knowledge_engine = (

            GeometryKnowledgeEngine()

        )

    def suggest(

        self,

        project

    ):

        suggestions = []

        knowledge = (

            self.knowledge_engine.get()

        )

        if (

            project.schema.width

            >

            knowledge["max_width"]

        ):

            suggestions.append(

                ConfigurationSuggestion(

                    code="DIVISION_SUGGESTION",

                    message=(

                        "Rozważ podział konstrukcji "

                        "na kilka pól"

                    )

                )

            )

        if (

            project.schema.height

            >

            knowledge["max_height"]

        ):

            suggestions.append(

                ConfigurationSuggestion(

                    code="HEIGHT_SUGGESTION",

                    message=(

                        "Rozważ zastosowanie "

                        "nadświetla"

                    )

                )

            )

        return suggestions