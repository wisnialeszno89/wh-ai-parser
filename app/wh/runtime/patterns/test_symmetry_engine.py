from types import SimpleNamespace

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.patterns.symmetry_engine import (
    SymmetryEngine
)


def test_symmetry_engine():

    f1 = Field(

        id=1,

        x=500,

        y=300

    )

    f2 = Field(

        id=2,

        x=1000,

        y=300

    )

    construction = (

        SimpleNamespace(

            topology=[

                [f1, f2],

                [f1, f2]

            ]

        )

    )

    engine = (

        SymmetryEngine()

    )

    assert (

        engine.is_horizontal_symmetric(

            construction

        )

        is True

    )

    assert (

        engine.is_vertical_symmetric(

            construction

        )

        is False

    )