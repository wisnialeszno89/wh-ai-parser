from app.wh.runtime.profile_knowledge_engine import (
    ProfileKnowledgeEngine
)


def test_profile_knowledge_engine():

    engine = (

        ProfileKnowledgeEngine()

    )

    knowledge = (

        engine.get(

            "Softline 82 MD"

        )

    )

    assert (

        knowledge[

            "supports_rc2"

        ]

        is True

    )

    assert (

        48

        in

        knowledge[

            "glass_packages_mm"

        ]

    )