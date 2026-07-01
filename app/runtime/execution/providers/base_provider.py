from abc import ABC, abstractmethod


class BaseToolProvider(ABC):

    @abstractmethod
    def locate(
        self,
        tool,
    ):
        pass