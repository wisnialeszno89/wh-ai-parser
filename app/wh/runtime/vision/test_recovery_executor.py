from app.wh.runtime.vision.recovery_executor import (
    RecoveryExecutor
)

from app.wh.runtime.vision.recovery_plan import (
    RecoveryPlan
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_executor():

    executor = (

        RecoveryExecutor()

    )

    plan = (

        RecoveryPlan(

            strategy=(

                AlternativeStrategy.CLICK_BY_COORDINATES

            ),

            reason="checkbox_failed"

        )

    )

    result = (

        executor.execute(

            plan

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.strategy

        ==

        AlternativeStrategy.CLICK_BY_COORDINATES

    )