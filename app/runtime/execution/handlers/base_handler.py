from abc import ABC
from abc import abstractmethod

from app.runtime.execution.handlers.handler_context import (
    HandlerContext,
)


class BaseHandler(ABC):

    @abstractmethod
    def execute(
        self,
        context: HandlerContext,
        payload,
    ):
        pass