from app.wh.runtime.topology.topology_signature_engine import (
    TopologySignatureEngine
)

from app.wh.runtime.patterns.topology_classifier import (
    TopologyClassifier
)

from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.construction_type_recognizer import (
    ConstructionTypeRecognizer
)

from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)

from app.wh.runtime.patterns.construction_reasoning_engine import (
    ConstructionReasoningEngine
)

from app.wh.runtime.construction_runtime import (
    ConstructionRuntime
)


class ConstructionPipeline:

    def __init__(

        self

    ):

        self.signature_engine = (

            TopologySignatureEngine()

        )

        self.classifier = (

            TopologyClassifier()

        )

        self.type_recognizer = (

            ConstructionTypeRecognizer()

        )

        self.runtime = (

            ConstructionRuntime()

        )

    def execute(

        self,

        construction

    ):

        signature = (

            self.signature_engine.build(

                construction

            )

        )

        labels = (

            self.classifier.classify(

                signature

            )

        )

        classification_context = (

            ClassificationContext(

                labels

            )

        )

        types = (

            self.type_recognizer.recognize(

                classification_context

            )

        )

        knowledge_context = (

            ConstructionKnowledgeContext(

                types

            )

        )

        reasoning = (

            ConstructionReasoningEngine(

                knowledge_context

            )

        )

        return self.runtime.execute(

            reasoning,

            construction

        )