from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)


def test_construction_reasoning_engine():

    context = (

        ConstructionKnowledgeContext(

            [

                "BALANCED_GRID_CONSTRUCTION",

                "SYMMETRIC_CONSTRUCTION"

            ]

        )

    )

    reasoning = (

        ConstructionReasoningEngine(

            context

        )

    )

    assert (

        reasoning.is_balanced()

        is True

    )

    assert (

        reasoning.is_symmetric()

        is True

    )

    assert (

        reasoning.is_single_row()

        is False

    )

    assert (

        reasoning.is_single_column()

        is False

    )