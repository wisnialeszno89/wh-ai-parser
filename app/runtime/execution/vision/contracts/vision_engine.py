from abc import ABC
from abc import abstractmethod

from app.runtime.execution.vision.models.vision_context import (
    VisionContext,
)


class VisionEngine(ABC):

    @abstractmethod
    def observe(
        self,
    ) -> VisionContext:

        ...