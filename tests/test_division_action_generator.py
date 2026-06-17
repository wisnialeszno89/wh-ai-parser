from app.wh.runtime.division_action_generator import (
    DivisionActionGenerator
)


def test_division_action_generator():

    generator = DivisionActionGenerator()

    actions = generator.generate(

        [

            450,

            1050

        ]

    )

    assert actions == [

        (

            "sash",

            450

        ),

        (

            "glass",

            450

        ),

        (

            "sash",

            1050

        ),

        (

            "glass",

            1050

        )

    ]