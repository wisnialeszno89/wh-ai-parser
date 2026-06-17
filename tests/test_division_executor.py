from app.wh.runtime.division_executor import (
    DivisionExecutor
)


def test_division_executor():

    executor = DivisionExecutor()

    actions = [

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

        )

    ]

    result = executor.execute(

        actions

    )

    assert result == [

        (

            450,

            600

        ),

        (

            450,

            600

        ),

        (

            1050,

            600

        )

    ]