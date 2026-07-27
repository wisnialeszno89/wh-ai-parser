from __future__ import annotations

from abc import ABC, abstractmethod

from app.runtime.execution.execution_result import ExecutionResult
from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


class InteractionExecutor(ABC):
    """
    Bazowy kontrakt dla wszystkich executorów Runtime.

    Każdy executor wykonuje dokładnie jeden typ akcji
    (CLICK, WRITE, VERIFY itd.) i zwraca ExecutionResult.
    """

    @abstractmethod
    def execute(
        self,
        context,
        step: InteractionStep,
    ) -> ExecutionResult:
        """Execute one interaction step."""
        raise NotImplementedError