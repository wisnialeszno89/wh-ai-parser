from app.wh.runtime.grid_division_engine import (
    GridDivisionEngine
)


def test_grid_division_engine():

    engine = GridDivisionEngine()

    result = engine.build_grid(

        [

            550,

            1150

        ],

        [

            700

        ]

    )

    assert result == [

        (

            550,

            700

        ),

        (

            1150,

            700

        )

    ]