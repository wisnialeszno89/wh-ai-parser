from app.wh.runtime.transoms.transom_executor import (
    TransomExecutor
)

from app.wh.runtime.transoms.transom import (
    Transom
)


def test_transom_executor():

    executor = TransomExecutor()

    transoms = [

        Transom(

            top_field=0,

            bottom_field=1

        )

    ]

    result = executor.execute(

        transoms

    )

    assert result is True