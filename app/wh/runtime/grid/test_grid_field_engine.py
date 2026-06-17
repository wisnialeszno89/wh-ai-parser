from app.wh.runtime.grid.grid_field_engine import (
    GridFieldEngine
)


def test_grid_field_engine():

    engine = GridFieldEngine()

    fields = engine.build(

        ratio_x=[0.5],

        ratio_y=[0.5]

    )

    assert len(

        fields

    ) == 4

    assert fields[0].id == 1

    assert fields[1].id == 2

    assert fields[2].id == 3

    assert fields[3].id == 4