from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)


def test_classification_context():

    context = (

        ClassificationContext(

            [

                "balanced_grid",

                "symmetric"

            ]

        )

    )

    assert (

        context.has(

            "balanced_grid"

        )

        is True

    )

    assert (

        context.has(

            "single_row"

        )

        is False

    )

    assert (

        context.has_any(

            "single_row",

            "symmetric"

        )

        is True

    )

    assert (

        context.has_all(

            "balanced_grid",

            "symmetric"

        )

        is True

    )