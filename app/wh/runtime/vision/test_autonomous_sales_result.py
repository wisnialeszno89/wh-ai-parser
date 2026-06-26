from app.wh.runtime.vision.autonomous_sales_result import (
    AutonomousSalesResult
)


def test_autonomous_sales_result():

    result = (

        AutonomousSalesResult(

            success=True,

            message="pipeline completed"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.message

        ==

        "pipeline completed"

    )