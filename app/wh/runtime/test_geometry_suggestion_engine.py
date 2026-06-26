from app.wh.runtime.geometry_suggestion_engine import (
    GeometrySuggestionEngine
)

from app.wh.runtime.construction_project import (
    ConstructionProject
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_geometry_suggestion_engine():

    project = (

        ConstructionProject(

            schema=ConstructionSchema(

                width=5000,

                height=1400,

                schema="RU+FIX+RU"

            ),

            offer=ConstructionOffer()

        )

    )

    engine = (

        GeometrySuggestionEngine()

    )

    suggestions = (

        engine.suggest(

            project

        )

    )

    assert len(

        suggestions

    ) == 1

    assert (

        suggestions[0]

        .code

        ==

        "DIVISION_SUGGESTION"

    )