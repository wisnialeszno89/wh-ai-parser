from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


@dataclass
class CustomerPredictionPipelineResult:

    prediction: CustomerPrediction