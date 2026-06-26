from app.wh.runtime.vision.self_optimization_report import (
    SelfOptimizationReport
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_self_optimization_report():

    report = (

        SelfOptimizationReport(

            confidence_level=(

                ConfidenceLevel.HIGH

            ),

            total_recovery_patterns=10,

            total_meta_patterns=5

        )

    )

    assert (

        report.confidence_level

        ==

        ConfidenceLevel.HIGH

    )

    assert (

        report.total_recovery_patterns

        ==

        10

    )

    assert (

        report.total_meta_patterns

        ==

        5

    )