from app.wh.runtime.transoms.transom import (
    Transom
)


def test_transom():

    transom = Transom(

        top_field=0,

        bottom_field=1

    )

    assert transom.top_field == 0

    assert transom.bottom_field == 1