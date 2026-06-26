from app.wh.runtime.construction_features import (
    ConstructionFeatures
)


def test_construction_features():

    features = (

        ConstructionFeatures(

            color_inside="anthracite",

            color_outside="anthracite",

            glass="3glass",

            warm_edge=True

        )

    )

    assert features.color_inside == (

        "anthracite"

    )

    assert features.color_outside == (

        "anthracite"

    )

    assert features.glass == (

        "3glass"

    )

    assert features.warm_edge is True