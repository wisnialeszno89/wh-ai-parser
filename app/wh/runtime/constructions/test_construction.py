from app.wh.runtime.constructions.construction import (
    Construction
)


def test_construction():

    construction = Construction()

    assert construction.fields == []

    assert construction.mullions == []

    assert construction.transoms == []