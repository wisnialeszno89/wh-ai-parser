from app.wh.runtime.vision.customer_knowledge_engine import (
    CustomerKnowledgeEngine
)

from app.wh.runtime.vision.customer_preference_engine import (
    CustomerPreferenceEngine
)

from app.wh.runtime.vision.customer_prediction_engine import (
    CustomerPredictionEngine
)

from app.wh.runtime.vision.customer_prediction_pipeline import (
    CustomerPredictionPipeline
)

from app.wh.runtime.vision.customer_recognizer import (
    CustomerRecognizer
)


class CustomerSubsystem:

    def __init__(

        self,

        brain

    ):

        self.customer_recognizer = (

            CustomerRecognizer()

        )

        self.customer_knowledge_engine = (

            CustomerKnowledgeEngine()

        )

        self.customer_preference_engine = (

            CustomerPreferenceEngine()

        )

        self.customer_prediction_engine = (

            CustomerPredictionEngine()

        )

        self.customer_prediction_pipeline = (

            CustomerPredictionPipeline(

                brain

            )

        )