from app.wh.runtime.construction_enricher import (
    ConstructionEnricher
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.construction_features import (
    ConstructionFeatures
)


def test_construction_enricher():

    enricher = (

        ConstructionEnricher()

    )

    construction = (

        ConstructionSchema(

            width=1800,

            height=1400,

            schema="RU+FIX+RU"

        )

    )

    features = (

        ConstructionFeatures(

            color_inside="anthracite",

            color_outside="anthracite",

            glass="3glass",

            warm_edge=True

        )

    )

    result = (

        enricher.enrich(

            construction,

            features

        )

    )

    assert (

        result.color_inside

        == "anthracite"

    )

    assert (

        result.color_outside

        == "anthracite"

    )

    assert (

        result.glass

        == "3glass"

    )

    assert (

        result.warm_edge

        is True

    )