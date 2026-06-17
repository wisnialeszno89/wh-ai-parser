from app.wh.runtime.construction_runtime import (
    ConstructionRuntime
)

from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)


def test_construction_runtime():

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

    runtime = (

        ConstructionRuntime()

    )

    result = runtime.execute(

        reasoning,

        {}

    )

    assert result is True