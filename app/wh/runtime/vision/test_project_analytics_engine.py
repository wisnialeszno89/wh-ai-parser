from app.wh.runtime.vision.project_analytics_engine import (
    ProjectAnalyticsEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.project_outcome import (
    ProjectOutcome
)


def test_project_analytics_engine():

    brain = (

        ProjectBrain()

    )

    brain.project_execution_history.remember(

        ProjectOutcome(

            project_name="offer_001",

            success=True,

            execution_time_seconds=10,

            error_count=1

        )

    )

    brain.project_execution_history.remember(

        ProjectOutcome(

            project_name="offer_002",

            success=False,

            execution_time_seconds=20,

            error_count=3

        )

    )

    engine = (

        ProjectAnalyticsEngine()

    )

    analytics = (

        engine.analyze(

            brain

        )

    )

    assert (

        analytics.total_projects

        ==

        2

    )

    assert (

        analytics.successful_projects

        ==

        1

    )

    assert (

        analytics.failed_projects

        ==

        1

    )

    assert (

        analytics.average_execution_time

        ==

        15

    )

    assert (

        analytics.average_error_count

        ==

        2

    )