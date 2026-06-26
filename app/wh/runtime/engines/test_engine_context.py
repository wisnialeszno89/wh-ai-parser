from app.wh.runtime.engines.engine_context import (
    EngineContext
)

from app.wh.runtime.engines.hst_engine import (
    HSTEngine
)


def test_engine_context():

    engine = (

        HSTEngine()

    )

    context = (

        EngineContext(

            engine

        )

    )

    assert (

        context.name()

        ==

        "HSTEngine"

    )

    result = (

        context.execute(

            {}

        )

    )

    assert [

        action.name

        for action

        in result.actions

    ] == [

        "frame",

        "glass"

    ]