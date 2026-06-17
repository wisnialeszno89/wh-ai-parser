from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)

from app.wh.runtime.patterns.psk_recognizer import (
    PSKRecognizer
)


def test_psk_recognizer():

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

    recognizer = (

        PSKRecognizer()

    )

    assert (

        recognizer.matches(

            reasoning

        )

        is True

    )

    assert (

        recognizer.name()

        == "PSK"

    )