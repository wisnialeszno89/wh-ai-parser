from app.wh.runtime.construction_strategy_factory import (
    ConstructionStrategyFactory
)

from app.wh.runtime.hst_construction_strategy import (
    HSTConstructionStrategy
)

from app.wh.runtime.window_construction_strategy import (
    WindowConstructionStrategy
)


def test_construction_strategy_factory():

    factory = (

        ConstructionStrategyFactory()

    )

    assert isinstance(

        factory.create(

            "window"

        ),

        WindowConstructionStrategy

    )

    assert isinstance(

        factory.create(

            "hst"

        ),

        HSTConstructionStrategy

    )