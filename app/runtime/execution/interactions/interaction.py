from abc import ABC, abstractmethod


class Interaction(ABC):

    @abstractmethod
    def execute(
        self,
        runtime,
    ):
        pass