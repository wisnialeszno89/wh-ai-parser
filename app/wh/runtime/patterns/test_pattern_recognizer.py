from types import SimpleNamespace

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.patterns.pattern_recognizer import (
    PatternRecognizer
)


def test_pattern_recognizer():

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

    f3 = Field(

        id=3,

        x=500,

        y=700

    )

    f4 = Field(

        id=4,

        x=1000,

        y=700

    )

    construction = (

        SimpleNamespace(

            topology=[

                [f1, f2],

                [f3, f4]

            ]

        )

    )

    recognizer = (

        PatternRecognizer()

    )

    assert (

        recognizer.is_2x2(

            construction

        )

        is True

    )

    assert (

        recognizer.is_balanced(

            construction

        )

        is True

    )

    assert (

        recognizer.is_single_row(

            construction

        )

        is False

    )

    assert (

        recognizer.is_single_column(

            construction

        )

        is False

    )