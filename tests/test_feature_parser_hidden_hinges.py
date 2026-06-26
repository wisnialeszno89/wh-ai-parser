from app.wh.runtime.feature_parser import (
    FeatureParser
)


def test_feature_parser_hidden_hinges():

    parser = (

        FeatureParser()

    )

    features = (

        parser.parse(

            """

            ukryte zawiasy

            """

        )

    )

    assert (

        features.hidden_hinges

        is True

    )