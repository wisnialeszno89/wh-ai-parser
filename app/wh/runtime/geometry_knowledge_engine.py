from app.wh.runtime.geometry_knowledge import (
    GEOMETRY_KNOWLEDGE
)


class GeometryKnowledgeEngine:

    def get(

        self,

        construction_type="default"

    ):

        return (

            GEOMETRY_KNOWLEDGE.get(

                construction_type,

                GEOMETRY_KNOWLEDGE[

                    "default"

                ]

            )

        )