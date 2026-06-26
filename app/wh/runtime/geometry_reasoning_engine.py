from app.wh.runtime.configuration_problem import (
    ConfigurationProblem
)

from app.wh.runtime.geometry_knowledge_engine import (
    GeometryKnowledgeEngine
)


class GeometryReasoningEngine:

    def __init__(

        self

    ):

        self.knowledge_engine = (

            GeometryKnowledgeEngine()

        )

    def validate(

        self,

        project

    ):

        problems = []

        knowledge = (

            self.knowledge_engine.get()

        )

        if (

            project.schema.width

            >

            knowledge["max_width"]

        ):

            problems.append(

                ConfigurationProblem(

                    code="WIDTH_EXCEEDED",

                    message=(

                        f"Szerokość "

                        f"{project.schema.width} mm "

                        f"przekracza "

                        f"dopuszczalne "

                        f"{knowledge['max_width']} mm"

                    )

                )

            )

        if (

            project.schema.height

            >

            knowledge["max_height"]

        ):

            problems.append(

                ConfigurationProblem(

                    code="HEIGHT_EXCEEDED",

                    message=(

                        f"Wysokość "

                        f"{project.schema.height} mm "

                        f"przekracza "

                        f"dopuszczalne "

                        f"{knowledge['max_height']} mm"

                    )

                )

            )

        return problems