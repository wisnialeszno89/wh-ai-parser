from app.wh.runtime.feature_parser import (
    FeatureParser
)


def test_feature_parser_v_perfect():

    parser = (

        FeatureParser()

    )

    features = (

        parser.parse(

            """

            V-perfect

            """

        )

    )

    assert (

        features.v_perfect

        is True

    )