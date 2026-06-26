from app.wh.runtime.feature_parser import (
    FeatureParser
)


def test_feature_parser_swisspacer():

    parser = (

        FeatureParser()

    )

    features = (

        parser.parse(

            """

            Swisspacer Ultimate

            """

        )

    )

    assert (

        features.swisspacer

        is True

    )