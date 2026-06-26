from app.wh.runtime.feature_parser import (
    FeatureParser
)


def test_feature_parser():

    parser = (

        FeatureParser()

    )

    features = (

        parser.parse(

            """
            1800x1400 RU FIX RU
            antracyt obustronny
            3 szyby
            ciepła ramka
            """

        )

    )

    assert (

        features.color_inside

        == "anthracite"

    )

    assert (

        features.color_outside

        == "anthracite"

    )

    assert (

        features.glass

        == "3glass"

    )

    assert (

        features.warm_edge

        is True

    )