from app.wh.knowledge.services.knowledge_engine import (
    KnowledgeEngine
)


def test_choose_profile():

    engine = (

        KnowledgeEngine()

    )

    decision = (

        engine.choose_profile(

            security="RC2",

            glazing="Triple"

        )

    )

    assert decision.profile == "VEKA Softline 82 MD"

    assert decision.confidence == 1.0

    assert "supports" in decision.explanation