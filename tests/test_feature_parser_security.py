from app.wh.runtime.feature_parser import (
    FeatureParser
)


def test_feature_parser_security():

    parser = (

        FeatureParser()

    )

    features = (

        parser.parse(

            """
            kontaktrony
            P4
            RC2
            48 mm
            """

        )

    )

    assert (

        features.contacts

        is True

    )

    assert (

        features.security_glass_p4

        is True

    )

    assert (

        features.security_class_rc2

        is True

    )

    assert (

        features.glass_package_mm

        == 48

    )