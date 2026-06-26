from app.wh.runtime.vision.cognitive_loop_report import (
    CognitiveLoopReport
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_cognitive_loop_report():

    report = (

        CognitiveLoopReport(

            confidence_level=(

                ConfidenceLevel.HIGH

            ),

            recovery_patterns=10,

            meta_patterns=5

        )

    )

    assert (

        report.confidence_level

        ==

        ConfidenceLevel.HIGH

    )

    assert (

        report.recovery_patterns

        ==

        10

    )

    assert (

        report.meta_patterns

        ==

        5

    )