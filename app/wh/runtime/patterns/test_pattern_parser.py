from app.wh.runtime.patterns.pattern_parser import (
    PatternParser
)


def test_pattern_parser():

    parser = PatternParser()

    result = parser.parse(

        "RU|FIX"

    )

    assert result == [

        [

            "RU",

            "FIX"

        ]

    ]


def test_pattern_parser_two_rows():

    parser = PatternParser()

    result = parser.parse(

        "RU|FIX/FIX|RU"

    )

    assert result == [

        [

            "RU",

            "FIX"

        ],

        [

            "FIX",

            "RU"

        ]

    ]