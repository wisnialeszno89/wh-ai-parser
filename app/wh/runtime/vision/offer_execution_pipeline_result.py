from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


@dataclass
class OfferExecutionPipelineResult:

    execution_result: IntelligentVisionExecutionResult