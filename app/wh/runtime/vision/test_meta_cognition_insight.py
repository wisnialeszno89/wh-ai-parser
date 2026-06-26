from app.wh.runtime.vision.meta_cognition_insight import (
    MetaCognitionInsight
)


def test_meta_cognition_insight():

    insight = (

        MetaCognitionInsight(

            total_reflections=100,

            total_successes=80,

            total_failures=20,

            success_rate=0.8

        )

    )

    assert (

        insight.total_reflections

        ==

        100

    )

    assert (

        insight.success_rate

        ==

        0.8

    )