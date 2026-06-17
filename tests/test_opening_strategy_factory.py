from app.wh.model.opening import (
    Opening
)

from app.wh.runtime.fix_strategy import (
    FixStrategy
)

from app.wh.runtime.hst_strategy import (
    HSTStrategy
)

from app.wh.runtime.opening_strategy_factory import (
    OpeningStrategyFactory
)

from app.wh.runtime.tilt_turn_strategy import (
    TiltTurnStrategy
)


def test_opening_strategy_factory():

    factory = (

        OpeningStrategyFactory()

    )

    assert isinstance(

        factory.create(

            Opening.FIX

        ),

        FixStrategy

    )

    assert isinstance(

        factory.create(

            Opening.TILT_TURN

        ),

        TiltTurnStrategy

    )

    assert isinstance(

        factory.create(

            Opening.HST

        ),

        HSTStrategy

    )