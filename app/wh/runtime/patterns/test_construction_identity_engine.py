from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)

from app.wh.runtime.patterns.construction_identity_engine import (
    ConstructionIdentityEngine
)


def test_construction_identity_engine():

    context = (

        ConstructionKnowledgeContext(

            [

                "SINGLE_ROW_CONSTRUCTION",

                "SYMMETRIC_CONSTRUCTION"

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

    result = identity.identify(

        reasoning

    )

    assert result == "HST"