from app.wh.runtime.position_creator import (
    PositionCreator
)


def test_position_creator():

    creator = PositionCreator()

    result = creator.create(

        1500,

        1400

    )

    print()

    print(result)

    assert result.confidence > 0.8