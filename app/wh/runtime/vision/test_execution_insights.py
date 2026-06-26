from app.wh.runtime.vision.execution_insights import (
    ExecutionInsights
)


def test_execution_insights():

    insights = (

        ExecutionInsights()

    )

    insights.success_rate = 95.0

    insights.most_common_failure_reason = (

        "database_error"

    )

    insights.human_review_count = 2

    insights.failed_goal_count = 3

    assert (

        insights.success_rate

        ==

        95.0

    )

    assert (

        insights.most_common_failure_reason

        ==

        "database_error"

    )

    assert (

        insights.human_review_count

        ==

        2

    )

    assert (

        insights.failed_goal_count

        ==

        3

    )