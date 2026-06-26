from app.wh.runtime.vision.recovery_knowledge import (
    RecoveryKnowledge
)


def test_recovery_knowledge():

    knowledge = (

        RecoveryKnowledge(

            failure_reason="OCR_ERROR",

            recovery_strategy="OCR_FALLBACK",

            success_count=12,

            failure_count=1

        )

    )

    assert (

        knowledge.failure_reason

        ==

        "OCR_ERROR"

    )

    assert (

        knowledge.recovery_strategy

        ==

        "OCR_FALLBACK"

    )

    assert (

        knowledge.success_count

        ==

        12

    )