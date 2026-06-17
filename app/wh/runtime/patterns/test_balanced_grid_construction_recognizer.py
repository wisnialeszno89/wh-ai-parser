from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.balanced_grid_construction_recognizer import (
    BalancedGridConstructionRecognizer
)


def test_balanced_grid_construction_recognizer():

    context = (

        ClassificationContext(

            [

                "balanced_grid"

            ]

        )

    )

    recognizer = (

        BalancedGridConstructionRecognizer()

    )

    assert (

        recognizer.matches(

            context

        )

        is True

    )

    assert (

        recognizer.name()

        ==

        "BALANCED_GRID_CONSTRUCTION"

    )