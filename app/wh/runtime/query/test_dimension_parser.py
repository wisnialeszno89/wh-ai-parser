from app.wh.runtime.query.dimension_parser import (
    DimensionParser
)


def test_dimension_parser():

    parser = DimensionParser()

    width, height = parser.parse(

        "2000x1500"

    )

    assert width == 2000

    assert height == 1500


def test_dimension_parser_spaces():

    parser = DimensionParser()

    width, height = parser.parse(

        "2000 x 1500"

    )

    assert width == 2000

    assert height == 1500


def test_dimension_parser_na():

    parser = DimensionParser()

    width, height = parser.parse(

        "2000 na 1500"

    )

    assert width == 2000

    assert height == 1500