from app.wh.runtime.vision.requirement_extractor import (
    RequirementExtractor
)


def test_requirement_extractor():

    extractor = (

        RequirementExtractor()

    )

    requirements = (

        extractor.extract(

            """

            Please prepare quotation.

            8 windows

            2 balcony doors

            Anthracite outside

            White inside

            Triple glazing

            RC2

            """

        )

    )

    assert requirements.windows == 8

    assert requirements.balcony_doors == 2

    assert requirements.outside_color == "Anthracite"

    assert requirements.inside_color == "White"

    assert requirements.glazing == "Triple"

    assert requirements.security == "RC2"