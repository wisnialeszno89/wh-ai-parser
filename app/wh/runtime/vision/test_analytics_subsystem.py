from app.wh.runtime.vision.analytics_subsystem import (
    AnalyticsSubsystem
)


def test_analytics_subsystem():

    subsystem = (

        AnalyticsSubsystem()

    )

    assert (

        subsystem.project_analytics_engine

        is not None

    )