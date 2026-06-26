from app.wh.runtime.construction_request_parser import (
    ConstructionRequestParser
)


def test_construction_request_parser():

    parser = (

        ConstructionRequestParser()

    )

    request = (

        parser.parse(

            "1800x1400 RU FIX RU"

        )

    )

    assert request.width == 1800

    assert request.height == 1400

    assert request.notation == (

        "RU FIX RU"

    )