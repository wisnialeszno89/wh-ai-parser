from app.wh.runtime.horizontal_division_action_generator import (
    HorizontalDivisionActionGenerator
)


def test_horizontal_division_action_generator():

    generator = HorizontalDivisionActionGenerator()

    actions = generator.generate(

        [

            700

        ]

    )

    assert actions == [

        (

            "sash_horizontal",

            700

        ),

        (

            "glass_horizontal",

            700

        )

    ]