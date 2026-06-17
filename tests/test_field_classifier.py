from app.wh.runtime.field_classifier import (
    FieldClassifier
)


def test_field_classifier():

    classifier = FieldClassifier()

    fields = [

        {

            "id":1,

            "x":550,

            "y":700,

            "type":"unknown"

        },

        {

            "id":2,

            "x":1150,

            "y":700,

            "type":"unknown"

        }

    ]

    result = classifier.classify(

        fields,

        "basic_window"

    )

    assert result[0]["type"] == "active"

    assert result[1]["type"] == "fixed"