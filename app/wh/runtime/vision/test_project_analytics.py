from app.wh.runtime.vision.project_analytics import (
    ProjectAnalytics
)


def test_project_analytics():

    analytics = (

        ProjectAnalytics(

            total_projects=100,

            successful_projects=97,

            failed_projects=3,

            success_rate=0.97,

            average_execution_time=15.2,

            average_error_count=0.3

        )

    )

    assert (

        analytics.total_projects

        ==

        100

    )

    assert (

        analytics.success_rate

        ==

        0.97

    )