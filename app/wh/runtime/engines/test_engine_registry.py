from app.wh.runtime.engines.engine_registry import (
    EngineRegistry
)

from app.wh.runtime.engines.hst_engine import (
    HSTEngine
)


def test_engine_registry():

    registry = EngineRegistry()

    engine = registry.get(

        "HST"

    )

    assert isinstance(

        engine,

        HSTEngine

    )