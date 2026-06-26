from app.wh.runtime.vision.recovery_knowledge_base import (
    RecoveryKnowledgeBase
)


def test_recovery_knowledge_base():

    kb = (

        RecoveryKnowledgeBase()

    )

    kb.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    knowledge = (

        kb.get(

            "OCR_ERROR",

            "OCR_FALLBACK"

        )

    )

    assert (

        knowledge.success_count

        ==

        1

    )

    assert (

        knowledge.failure_count

        ==

        0

    )