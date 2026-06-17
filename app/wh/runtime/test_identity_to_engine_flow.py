from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)

from app.wh.runtime.patterns.construction_identity_engine import (
    ConstructionIdentityEngine
)

from app.wh.runtime.engines.engine_factory import (
    EngineFactory
)

from app.wh.runtime.engines.psk_engine import (
    PSKEngine
)


def test_identity_to_engine_flow():

    context = (

        ConstructionKnowledgeContext(

            [

                "SINGLE_ROW_CONSTRUCTION"

            ]

        )

    )

    reasoning = (

        ConstructionReasoningEngine(

            context

        )

    )

    identity = (

        ConstructionIdentityEngine()

    )

    result = (

        identity.identify(

            reasoning

        )

    )

    factory = (

        EngineFactory()

    )

    engine = (

        factory.create(

            result

        )

    )

    assert result == "PSK"

    assert isinstance(

        engine,

        PSKEngine

    )