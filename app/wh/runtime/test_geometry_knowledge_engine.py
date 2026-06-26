from app.wh.runtime.geometry_knowledge_engine import (
    GeometryKnowledgeEngine
)


def test_geometry_knowledge_engine():

    engine = (

        GeometryKnowledgeEngine()

    )

    knowledge = (

        engine.get()

    )

    assert (

        knowledge[

            "max_width"

        ]

        ==

        4000

    )

    assert (

        knowledge[

            "max_height"

        ]

        ==

        3000

    )