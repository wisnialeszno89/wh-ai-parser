from app.wh.runtime.field_classifier import (
    FieldClassifier
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


def test_field_classifier():

    classifier = FieldClassifier()

    fields = [

        Field(

            id=1,

            x=550,

            y=700

        ),

        Field(

            id=2,

            x=1150,

            y=700

        )

    ]

    schema = ConstructionSchema(

        width=2000,

        height=1500,

        schema="basic_window",

        segments=[

            Segment(

                opening=TILT_TURN,

                width_ratio=0.5

            ),

            Segment(

                opening=FIX,

                width_ratio=0.5

            )

        ]

    )

    result = classifier.classify(

        fields,

        schema

    )

    assert (

        result[0].opening

        == TILT_TURN

    )

    assert (

        result[1].opening

        == FIX

    )