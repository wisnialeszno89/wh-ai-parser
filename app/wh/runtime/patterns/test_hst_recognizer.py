from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)

from app.wh.runtime.patterns.hst_recognizer import (
    HSTRecognizer
)


def test_hst_recognizer():

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

    recognizer = (

        HSTRecognizer()

    )

    assert (

        recognizer.matches(

            reasoning

        )

        is True

    )

    assert (

        recognizer.name()

        == "HST"

    )