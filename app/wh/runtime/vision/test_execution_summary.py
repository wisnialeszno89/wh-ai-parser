from app.wh.runtime.vision.execution_summary import (
    ExecutionSummary
)


def test_execution_summary():

    summary = (

        ExecutionSummary()

    )

    summary.total_goals = 10

    summary.success_count = 8

    summary.human_review_count = 2

    assert (

        summary.total_goals

        ==

        10

    )

    assert (

        summary.success_count

        ==

        8

    )

    assert (

        summary.human_review_count

        ==

        2

    )