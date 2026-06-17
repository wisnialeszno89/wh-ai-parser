from app.wh.runtime.engines.engine_factory import (
    EngineFactory
)

from app.wh.runtime.engines.hst_engine import (
    HSTEngine
)


def test_engine_factory():

    factory = EngineFactory()

    engine = factory.create(

        "HST"

    )

    assert isinstance(

        engine,

        HSTEngine

    )