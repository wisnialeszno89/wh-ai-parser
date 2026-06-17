from app.wh.runtime.mullions.mullion_executor import (
    MullionExecutor
)

from app.wh.runtime.mullions.mullion import (
    Mullion
)


def test_mullion_executor():

    executor = MullionExecutor()

    mullions = [

        Mullion(

            left_field=0,

            right_field=1

        )

    ]

    result = executor.execute(

        mullions

    )

    assert result is True