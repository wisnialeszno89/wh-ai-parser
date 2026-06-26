from app.wh.runtime.vision.learning_from_failures_engine import (
    LearningFromFailuresEngine
)


def test_learning_from_failures_engine():

    engine = (

        LearningFromFailuresEngine()

    )

    engine.learn(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    assert (

        engine.total_records()

        ==

        1

    )

    assert (

        engine.records[0].failure_reason

        ==

        "OCR_ERROR"

    )

    assert (

        engine.records[0].recovery_strategy

        ==

        "OCR_FALLBACK"

    )